"""Evidence-grade reverse-flow volume analysis for Rincon Bayou.

Operates only on the finalized local NRHIS historical CSV through the sparse query
engine. Reverse-flow volume is integrated from the original instantaneous discharge
observations using piecewise-linear interpolation. No interpolation is performed
across data gaps larger than twice the configured observation cadence.
"""
from __future__ import annotations

import csv
import json
import math
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

from nrhis_analysis.usgs_history_query import (
    QueryError,
    atomic_write_text,
    load_sparse_index,
    normalize_window,
    query_history,
    sha256_file,
)

ANALYSIS_SCHEMA_VERSION = 1
BUILD_NUMBER = "098"
DISCHARGE_PARAMETER = "00060"
STAGE_PARAMETER = "00065"
DEFAULT_SITE_NO = "08211503"
DEFAULT_CADENCE_MINUTES = 15
DEFAULT_GAP_HOURS = 24.0
CFS_SECONDS_PER_ACRE_FOOT = 43560.0


@dataclass(frozen=True)
class Point:
    observed_at: datetime
    value: float


@dataclass(frozen=True)
class NegativePiece:
    start: datetime
    end: datetime
    q_start: float
    q_end: float
    minimum_discharge_cfs: float

    @property
    def reverse_volume_acft(self) -> float:
        seconds = (self.end - self.start).total_seconds()
        return -((self.q_start + self.q_end) / 2.0) * seconds / CFS_SECONDS_PER_ACRE_FOOT


@dataclass
class ReverseInterval:
    start: datetime
    end: datetime
    reverse_volume_acft: float
    minimum_discharge_cfs: float
    segment_count: int

    @property
    def duration_hours(self) -> float:
        return (self.end - self.start).total_seconds() / 3600.0

    @property
    def mean_reverse_discharge_cfs(self) -> float:
        seconds = (self.end - self.start).total_seconds()
        if seconds <= 0:
            return 0.0
        return -(self.reverse_volume_acft * CFS_SECONDS_PER_ACRE_FOOT / seconds)


def _parse_observed_at(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso_z(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_float(value: str) -> float | None:
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _iter_parameter(
    csv_path: Path,
    index_path: Path,
    *,
    start: str,
    end: str,
    site_no: str,
    parameter_code: str,
) -> Iterator[dict[str, str]]:
    return query_history(
        csv_path,
        index_path,
        start=start,
        end=end,
        site_nos=[site_no],
        parameter_codes=[parameter_code],
    )


def _atomic_write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _read_points(rows: Iterable[dict[str, str]]) -> list[Point]:
    points: list[Point] = []
    for row in rows:
        value = _parse_float(row.get("value", ""))
        if value is None:
            continue
        points.append(Point(_parse_observed_at(row["observed_at"]), value))
    return points


def _detect_material_gaps(
    points: list[Point], *, cadence: timedelta, gap_hours: float
) -> list[dict[str, Any]]:
    threshold = timedelta(hours=gap_hours)
    rows: list[dict[str, Any]] = []
    for previous, current in zip(points, points[1:]):
        delta = current.observed_at - previous.observed_at
        if delta < threshold:
            continue
        missing_slots = max(0, int(delta / cadence) - 1)
        rows.append(
            {
                "previous_observed_at": previous.observed_at,
                "next_observed_at": current.observed_at,
                "missing_start": previous.observed_at + cadence,
                "missing_end_exclusive": current.observed_at,
                "gap_hours": delta.total_seconds() / 3600.0,
                "missing_slots": missing_slots,
            }
        )
    return rows


def _negative_piece(
    p0: Point, p1: Point, *, max_delta: timedelta
) -> NegativePiece | None:
    """Return the negative portion of a linearly interpolated observation pair."""
    dt = p1.observed_at - p0.observed_at
    if dt <= timedelta(0) or dt > max_delta:
        return None
    q0, q1 = p0.value, p1.value
    if q0 >= 0 and q1 >= 0:
        return None

    seconds = dt.total_seconds()
    if q0 < 0 and q1 < 0:
        return NegativePiece(p0.observed_at, p1.observed_at, q0, q1, min(q0, q1))

    if q0 < 0 <= q1:
        fraction = (-q0) / (q1 - q0)
        end = p0.observed_at + timedelta(seconds=seconds * fraction)
        return NegativePiece(p0.observed_at, end, q0, 0.0, q0)

    # q0 >= 0 and q1 < 0
    fraction = q0 / (q0 - q1)
    start = p0.observed_at + timedelta(seconds=seconds * fraction)
    return NegativePiece(start, p1.observed_at, 0.0, q1, q1)


def _split_piece(
    start: datetime,
    end: datetime,
    q_start: float,
    q_end: float,
    boundaries: list[datetime],
) -> Iterator[tuple[datetime, datetime, float, float]]:
    """Split a linear discharge segment at requested boundaries."""
    cuts = [start] + [b for b in boundaries if start < b < end] + [end]
    total = (end - start).total_seconds()
    for left, right in zip(cuts, cuts[1:]):
        lf = (left - start).total_seconds() / total
        rf = (right - start).total_seconds() / total
        ql = q_start + (q_end - q_start) * lf
        qr = q_start + (q_end - q_start) * rf
        yield left, right, ql, qr


def _month_boundaries(start: datetime, end: datetime) -> list[datetime]:
    current = datetime(start.year, start.month, 1, tzinfo=timezone.utc)
    if current <= start:
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            current = datetime(current.year, current.month + 1, 1, tzinfo=timezone.utc)
    result: list[datetime] = []
    while current < end:
        result.append(current)
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            current = datetime(current.year, current.month + 1, 1, tzinfo=timezone.utc)
    return result


def _duration_class(hours: float) -> str:
    if hours < 1:
        return "<1 hour"
    if hours < 6:
        return "1-6 hours"
    if hours < 24:
        return "6-24 hours"
    if hours < 72:
        return "1-3 days"
    if hours < 168:
        return "3-7 days"
    return "7+ days"


def _integrate_reverse_flow(
    points: list[Point], *, cadence: timedelta
) -> tuple[list[ReverseInterval], list[NegativePiece]]:
    max_delta = cadence * 2
    intervals: list[ReverseInterval] = []
    pieces: list[NegativePiece] = []
    active: ReverseInterval | None = None
    for p0, p1 in zip(points, points[1:]):
        piece = _negative_piece(p0, p1, max_delta=max_delta)
        if piece is None:
            if active is not None:
                intervals.append(active)
                active = None
            continue
        pieces.append(piece)
        if active is not None and abs((piece.start - active.end).total_seconds()) <= 1.0:
            active.end = piece.end
            active.reverse_volume_acft += piece.reverse_volume_acft
            active.minimum_discharge_cfs = min(
                active.minimum_discharge_cfs, piece.minimum_discharge_cfs
            )
            active.segment_count += 1
        else:
            if active is not None:
                intervals.append(active)
            active = ReverseInterval(
                piece.start,
                piece.end,
                piece.reverse_volume_acft,
                piece.minimum_discharge_cfs,
                1,
            )
    if active is not None:
        intervals.append(active)
    return intervals, pieces


def _phase_definitions(
    effective_start: datetime,
    effective_end: datetime,
    gaps: list[dict[str, Any]],
    last_discharge: datetime | None,
    cadence: timedelta,
) -> list[dict[str, Any]]:
    longest = max(gaps, key=lambda item: item["gap_hours"], default=None)
    phases: list[dict[str, Any]] = []
    if longest is None:
        phases.append(
            {
                "phase": "observed_record",
                "start": effective_start,
                "end": min(effective_end, (last_discharge or effective_end) + cadence),
                "status": "observable",
            }
        )
    else:
        if effective_start < longest["missing_start"]:
            phases.append(
                {
                    "phase": "pre_gap",
                    "start": effective_start,
                    "end": longest["missing_start"],
                    "status": "observable",
                }
            )
        phases.append(
            {
                "phase": "discharge_gap",
                "start": longest["missing_start"],
                "end": longest["missing_end_exclusive"],
                "status": "not_observable_from_discharge",
            }
        )
        if last_discharge and longest["next_observed_at"] <= last_discharge:
            phases.append(
                {
                    "phase": "post_gap_pre_terminal",
                    "start": longest["next_observed_at"],
                    "end": min(effective_end, last_discharge + cadence),
                    "status": "observable",
                }
            )
    if last_discharge and last_discharge + cadence < effective_end:
        phases.append(
            {
                "phase": "post_terminal",
                "start": last_discharge + cadence,
                "end": effective_end,
                "status": "not_observable_from_discharge",
            }
        )
    return phases


def _phase_for_time(value: datetime, phases: list[dict[str, Any]]) -> dict[str, Any] | None:
    for phase in phases:
        if phase["start"] <= value < phase["end"]:
            return phase
    return None


def analyze_rincon_reverse_flow(
    csv_path: Path,
    index_path: Path,
    output_dir: Path,
    *,
    start: str,
    end: str,
    site_no: str = DEFAULT_SITE_NO,
    cadence_minutes: int = DEFAULT_CADENCE_MINUTES,
    gap_hours: float = DEFAULT_GAP_HOURS,
) -> dict[str, Any]:
    """Integrate reverse-direction discharge and summarize evidence windows."""
    if cadence_minutes < 1:
        raise QueryError("cadence_minutes must be at least 1")
    if gap_hours <= 0:
        raise QueryError("gap_hours must be greater than 0")

    index = load_sparse_index(index_path, csv_path)
    effective_start_text, effective_end_text = normalize_window(start, end)
    effective_start = _parse_observed_at(effective_start_text)
    effective_end = _parse_observed_at(effective_end_text)
    cadence = timedelta(minutes=cadence_minutes)

    points = _read_points(
        _iter_parameter(
            csv_path,
            index_path,
            start=start,
            end=end,
            site_no=site_no,
            parameter_code=DISCHARGE_PARAMETER,
        )
    )
    gaps = _detect_material_gaps(points, cadence=cadence, gap_hours=gap_hours)
    last_discharge = points[-1].observed_at if points else None
    intervals, negative_pieces = _integrate_reverse_flow(points, cadence=cadence)
    phases = _phase_definitions(effective_start, effective_end, gaps, last_discharge, cadence)

    # Stage counts by phase establish monitoring continuity without imputing discharge.
    stage_counts = {phase["phase"]: 0 for phase in phases}
    for row in _iter_parameter(
        csv_path,
        index_path,
        start=start,
        end=end,
        site_no=site_no,
        parameter_code=STAGE_PARAMETER,
    ):
        phase = _phase_for_time(_parse_observed_at(row["observed_at"]), phases)
        if phase is not None:
            stage_counts[phase["phase"]] += 1

    interval_rows: list[dict[str, Any]] = []
    monthly: dict[str, dict[str, float]] = {}
    phase_metrics: dict[str, dict[str, float]] = {
        phase["phase"]: {"reverse_volume_acft": 0.0, "reverse_hours": 0.0}
        for phase in phases
    }

    for interval in intervals:
        interval_rows.append(
            {
                "start": _iso_z(interval.start),
                "end": _iso_z(interval.end),
                "duration_hours": round(interval.duration_hours, 6),
                "segment_count": interval.segment_count,
                "minimum_discharge_cfs": round(interval.minimum_discharge_cfs, 6),
                "mean_reverse_discharge_cfs": round(interval.mean_reverse_discharge_cfs, 6),
                "reverse_volume_acft": round(interval.reverse_volume_acft, 6),
                "duration_class": _duration_class(interval.duration_hours),
            }
        )


    # Allocate the original linearly interpolated negative pieces exactly to calendar
    # months and evidence phases. Pieces are split at boundaries and re-integrated, so
    # monthly and phase volumes sum to the evidence-grade total without proportional
    # allocation approximations.
    phase_boundaries = sorted(
        {phase["start"] for phase in phases} | {phase["end"] for phase in phases}
    )
    for piece in negative_pieces:
        for left, right, q_left, q_right in _split_piece(
            piece.start,
            piece.end,
            piece.q_start,
            piece.q_end,
            _month_boundaries(piece.start, piece.end),
        ):
            seconds = (right - left).total_seconds()
            volume = -((q_left + q_right) / 2.0) * seconds / CFS_SECONDS_PER_ACRE_FOOT
            key = left.strftime("%Y-%m")
            bucket = monthly.setdefault(
                key, {"reverse_volume_acft": 0.0, "reverse_hours": 0.0}
            )
            bucket["reverse_volume_acft"] += volume
            bucket["reverse_hours"] += seconds / 3600.0

        for left, right, q_left, q_right in _split_piece(
            piece.start,
            piece.end,
            piece.q_start,
            piece.q_end,
            phase_boundaries,
        ):
            midpoint = left + (right - left) / 2
            phase = _phase_for_time(midpoint, phases)
            if phase is None or phase["status"] != "observable":
                continue
            seconds = (right - left).total_seconds()
            volume = -((q_left + q_right) / 2.0) * seconds / CFS_SECONDS_PER_ACRE_FOOT
            phase_metrics[phase["phase"]]["reverse_volume_acft"] += volume
            phase_metrics[phase["phase"]]["reverse_hours"] += seconds / 3600.0

    class_order = ["<1 hour", "1-6 hours", "6-24 hours", "1-3 days", "3-7 days", "7+ days"]
    duration_rows: list[dict[str, Any]] = []
    for label in class_order:
        selected = [row for row in interval_rows if row["duration_class"] == label]
        duration_rows.append(
            {
                "duration_class": label,
                "interval_count": len(selected),
                "total_reverse_hours": round(sum(float(row["duration_hours"]) for row in selected), 6),
                "reverse_volume_acft": round(sum(float(row["reverse_volume_acft"]) for row in selected), 6),
            }
        )

    monthly_rows = [
        {
            "month": month,
            "reverse_hours": round(values["reverse_hours"], 6),
            "reverse_volume_acft": round(values["reverse_volume_acft"], 6),
        }
        for month, values in sorted(monthly.items())
    ]

    phase_rows: list[dict[str, Any]] = []
    for phase in phases:
        metrics = phase_metrics[phase["phase"]]
        observable = phase["status"] == "observable"
        phase_rows.append(
            {
                "phase": phase["phase"],
                "start": _iso_z(phase["start"]),
                "end_exclusive": _iso_z(phase["end"]),
                "status": phase["status"],
                "stage_record_count": stage_counts[phase["phase"]],
                "reverse_hours": round(metrics["reverse_hours"], 6) if observable else "",
                "reverse_volume_acft": round(metrics["reverse_volume_acft"], 6) if observable else "",
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    intervals_csv = output_dir / "reverse_flow_intervals.csv"
    duration_csv = output_dir / "duration_classes.csv"
    monthly_csv = output_dir / "monthly_reverse_flow.csv"
    phases_csv = output_dir / "phase_summary.csv"
    summary_path = output_dir / "rincon_reverse_flow_summary.json"
    receipt_path = output_dir / "analysis-receipt.json"

    _atomic_write_csv(
        intervals_csv,
        [
            "start",
            "end",
            "duration_hours",
            "segment_count",
            "minimum_discharge_cfs",
            "mean_reverse_discharge_cfs",
            "reverse_volume_acft",
            "duration_class",
        ],
        interval_rows,
    )
    _atomic_write_csv(duration_csv, ["duration_class", "interval_count", "total_reverse_hours", "reverse_volume_acft"], duration_rows)
    _atomic_write_csv(monthly_csv, ["month", "reverse_hours", "reverse_volume_acft"], monthly_rows)
    _atomic_write_csv(phases_csv, ["phase", "start", "end_exclusive", "status", "stage_record_count", "reverse_hours", "reverse_volume_acft"], phase_rows)

    total_volume = sum(interval.reverse_volume_acft for interval in intervals)
    longest = max(interval_rows, key=lambda row: float(row["duration_hours"]), default=None)
    largest = max(interval_rows, key=lambda row: float(row["reverse_volume_acft"]), default=None)
    deepest = min(interval_rows, key=lambda row: float(row["minimum_discharge_cfs"]), default=None)
    longest_gap = max(gaps, key=lambda item: item["gap_hours"], default=None)
    gap_summary = None
    if longest_gap:
        gap_summary = {
            "previous_observed_at": _iso_z(longest_gap["previous_observed_at"]),
            "next_observed_at": _iso_z(longest_gap["next_observed_at"]),
            "missing_start": _iso_z(longest_gap["missing_start"]),
            "missing_end_exclusive": _iso_z(longest_gap["missing_end_exclusive"]),
            "gap_hours": round(float(longest_gap["gap_hours"]), 6),
            "missing_slots": int(longest_gap["missing_slots"]),
        }

    summary: dict[str, Any] = {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "build": BUILD_NUMBER,
        "analysis": "rincon_reverse_flow_volume",
        "query_mode": "local_finalized_archive",
        "network_requests_made": 0,
        "integration_method": "piecewise_linear_negative_portion",
        "interpolation_gap_limit_minutes": cadence_minutes * 2,
        "site_no": site_no,
        "requested_start": start,
        "requested_end": end,
        "effective_start": effective_start_text,
        "effective_end_exclusive": effective_end_text,
        "discharge_observation_count": len(points),
        "reverse_flow_interval_count": len(interval_rows),
        "total_reverse_flow_volume_acft": round(total_volume, 6),
        "longest_reverse_flow_interval": longest,
        "largest_reverse_flow_volume_interval": largest,
        "deepest_reverse_flow_interval": deepest,
        "longest_material_discharge_gap": gap_summary,
        "last_discharge_observed_at": _iso_z(last_discharge),
        "phase_summary": phase_rows,
        "duration_classes": duration_rows,
        "monthly_reverse_flow": monthly_rows,
    }
    atomic_write_text(summary_path, json.dumps(summary, indent=2, sort_keys=True) + "\n")

    receipt: dict[str, Any] = {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "build": BUILD_NUMBER,
        "analysis": "rincon_reverse_flow_volume",
        "created_at": _iso_z(datetime.now(timezone.utc)),
        "query_mode": "local_finalized_archive",
        "network_requests_made": 0,
        "source_csv": str(csv_path.resolve()),
        "source_csv_bytes": int(index["source_csv_bytes"]),
        "source_csv_sha256": str(index["source_csv_sha256"]),
        "query_index": str(index_path.resolve()),
        "query_index_sha256": sha256_file(index_path),
        "site_no": site_no,
        "requested_start": start,
        "requested_end": end,
        "summary": str(summary_path.resolve()),
        "summary_sha256": sha256_file(summary_path),
        "reverse_flow_intervals_csv": str(intervals_csv.resolve()),
        "reverse_flow_intervals_csv_sha256": sha256_file(intervals_csv),
        "duration_classes_csv": str(duration_csv.resolve()),
        "duration_classes_csv_sha256": sha256_file(duration_csv),
        "monthly_reverse_flow_csv": str(monthly_csv.resolve()),
        "monthly_reverse_flow_csv_sha256": sha256_file(monthly_csv),
        "phase_summary_csv": str(phases_csv.resolve()),
        "phase_summary_csv_sha256": sha256_file(phases_csv),
        "reverse_flow_interval_count": len(interval_rows),
        "total_reverse_flow_volume_acft": round(total_volume, 6),
        "last_discharge_observed_at": _iso_z(last_discharge),
    }
    atomic_write_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    receipt["receipt"] = str(receipt_path.resolve())
    return receipt
