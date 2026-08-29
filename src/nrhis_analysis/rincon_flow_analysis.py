"""Local-only Rincon Bayou discharge continuity and directional-flow analysis.

The analysis operates against the finalized NRHIS historical USGS CSV through the
bounded-memory query engine. It makes no network requests and writes evidence tables
plus a hash-bound receipt suitable for later review.
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
BUILD_NUMBER = "097"
DISCHARGE_PARAMETER = "00060"
STAGE_PARAMETER = "00065"
DEFAULT_SITE_NO = "08211503"
DEFAULT_CADENCE_MINUTES = 15
DEFAULT_GAP_HOURS = 24.0
DEFAULT_STAGE_CONTINUITY_RATIO = 0.80


@dataclass
class DischargeGap:
    previous_observed_at: datetime
    next_observed_at: datetime
    missing_start: datetime
    missing_end_exclusive: datetime
    missing_slots: int
    stage_records: int = 0

    @property
    def duration_hours(self) -> float:
        return (self.next_observed_at - self.previous_observed_at).total_seconds() / 3600.0

    def stage_coverage_ratio(self) -> float:
        if self.missing_slots <= 0:
            return 0.0
        return min(1.0, self.stage_records / self.missing_slots)


@dataclass
class NegativeInterval:
    start: datetime
    end: datetime
    count: int
    minimum_value: float
    sum_value: float

    @property
    def mean_value(self) -> float:
        return self.sum_value / self.count

    @property
    def duration_hours(self) -> float:
        return (self.end - self.start).total_seconds() / 3600.0


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
    raw = str(value).strip()
    if not raw:
        return None
    try:
        parsed = float(raw)
    except ValueError:
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


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


def _detect_discharge_gaps_and_negative_intervals(
    rows: Iterable[dict[str, str]],
    *,
    cadence_minutes: int,
    gap_hours: float,
) -> tuple[
    list[DischargeGap],
    list[NegativeInterval],
    int,
    datetime | None,
    datetime | None,
    float | None,
    float | None,
]:
    cadence = timedelta(minutes=cadence_minutes)
    minimum_gap = timedelta(hours=gap_hours)
    gaps: list[DischargeGap] = []
    negatives: list[NegativeInterval] = []
    record_count = 0
    first_time: datetime | None = None
    last_time: datetime | None = None
    minimum_value: float | None = None
    maximum_value: float | None = None
    previous_time: datetime | None = None
    active_negative: NegativeInterval | None = None

    for row in rows:
        observed = _parse_observed_at(row["observed_at"])
        value = _parse_float(row.get("value", ""))
        record_count += 1
        if first_time is None:
            first_time = observed
        last_time = observed

        if previous_time is not None:
            delta = observed - previous_time
            if delta >= minimum_gap:
                missing_slots = max(0, int(delta / cadence) - 1)
                gaps.append(
                    DischargeGap(
                        previous_observed_at=previous_time,
                        next_observed_at=observed,
                        missing_start=previous_time + cadence,
                        missing_end_exclusive=observed,
                        missing_slots=missing_slots,
                    )
                )
            if active_negative is not None and delta > cadence * 2:
                negatives.append(active_negative)
                active_negative = None

        if value is not None:
            minimum_value = value if minimum_value is None else min(minimum_value, value)
            maximum_value = value if maximum_value is None else max(maximum_value, value)
            if value < 0:
                if active_negative is None:
                    active_negative = NegativeInterval(
                        start=observed,
                        end=observed,
                        count=1,
                        minimum_value=value,
                        sum_value=value,
                    )
                else:
                    active_negative.end = observed
                    active_negative.count += 1
                    active_negative.minimum_value = min(active_negative.minimum_value, value)
                    active_negative.sum_value += value
            elif active_negative is not None:
                negatives.append(active_negative)
                active_negative = None
        elif active_negative is not None:
            negatives.append(active_negative)
            active_negative = None

        previous_time = observed

    if active_negative is not None:
        negatives.append(active_negative)

    return (
        gaps,
        negatives,
        record_count,
        first_time,
        last_time,
        minimum_value,
        maximum_value,
    )


def _apply_stage_coverage(
    gaps: list[DischargeGap],
    stage_rows: Iterable[dict[str, str]],
    *,
    last_discharge: datetime | None,
) -> dict[str, Any]:
    ordered_gaps = sorted(gaps, key=lambda gap: gap.missing_start)
    pointer = 0
    stage_count = 0
    first_stage: datetime | None = None
    last_stage: datetime | None = None
    first_stage_after_discharge: datetime | None = None
    stage_records_after_discharge = 0

    for row in stage_rows:
        observed = _parse_observed_at(row["observed_at"])
        stage_count += 1
        if first_stage is None:
            first_stage = observed
        last_stage = observed

        if last_discharge is not None and observed > last_discharge:
            stage_records_after_discharge += 1
            if first_stage_after_discharge is None:
                first_stage_after_discharge = observed

        while pointer < len(ordered_gaps) and observed >= ordered_gaps[pointer].missing_end_exclusive:
            pointer += 1
        if pointer < len(ordered_gaps):
            gap = ordered_gaps[pointer]
            if gap.missing_start <= observed < gap.missing_end_exclusive:
                gap.stage_records += 1

    return {
        "stage_record_count": stage_count,
        "first_stage_observed_at": _iso_z(first_stage),
        "last_stage_observed_at": _iso_z(last_stage),
        "first_stage_after_last_discharge": _iso_z(first_stage_after_discharge),
        "stage_records_after_last_discharge": stage_records_after_discharge,
    }


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


def analyze_rincon_flow(
    csv_path: Path,
    index_path: Path,
    output_dir: Path,
    *,
    start: str,
    end: str,
    site_no: str = DEFAULT_SITE_NO,
    cadence_minutes: int = DEFAULT_CADENCE_MINUTES,
    gap_hours: float = DEFAULT_GAP_HOURS,
    stage_continuity_ratio: float = DEFAULT_STAGE_CONTINUITY_RATIO,
) -> dict[str, Any]:
    """Analyze discharge gaps, stage continuity, termination, and negative flow."""

    if cadence_minutes < 1:
        raise QueryError("cadence_minutes must be at least 1")
    if gap_hours <= 0:
        raise QueryError("gap_hours must be greater than 0")
    if not 0 <= stage_continuity_ratio <= 1:
        raise QueryError("stage_continuity_ratio must be between 0 and 1")

    index = load_sparse_index(index_path, csv_path)
    effective_start, effective_end_exclusive = normalize_window(start, end)

    (
        gaps,
        negative_intervals,
        discharge_record_count,
        first_discharge,
        last_discharge,
        minimum_discharge,
        maximum_discharge,
    ) = _detect_discharge_gaps_and_negative_intervals(
        _iter_parameter(
            csv_path,
            index_path,
            start=start,
            end=end,
            site_no=site_no,
            parameter_code=DISCHARGE_PARAMETER,
        ),
        cadence_minutes=cadence_minutes,
        gap_hours=gap_hours,
    )

    stage_summary = _apply_stage_coverage(
        gaps,
        _iter_parameter(
            csv_path,
            index_path,
            start=start,
            end=end,
            site_no=site_no,
            parameter_code=STAGE_PARAMETER,
        ),
        last_discharge=last_discharge,
    )

    gap_rows: list[dict[str, Any]] = []
    for gap in gaps:
        coverage = gap.stage_coverage_ratio()
        gap_rows.append(
            {
                "previous_discharge_observed_at": _iso_z(gap.previous_observed_at),
                "next_discharge_observed_at": _iso_z(gap.next_observed_at),
                "missing_start": _iso_z(gap.missing_start),
                "missing_end_exclusive": _iso_z(gap.missing_end_exclusive),
                "gap_hours_between_observations": round(gap.duration_hours, 4),
                "missing_discharge_slots": gap.missing_slots,
                "stage_records_during_missing_slots": gap.stage_records,
                "stage_coverage_ratio": round(coverage, 6),
                "stage_continued": coverage >= stage_continuity_ratio,
            }
        )

    negative_rows: list[dict[str, Any]] = []
    for interval in negative_intervals:
        negative_rows.append(
            {
                "start": _iso_z(interval.start),
                "end": _iso_z(interval.end),
                "duration_hours": round(interval.duration_hours, 4),
                "observation_count": interval.count,
                "minimum_discharge_cfs": round(interval.minimum_value, 6),
                "mean_discharge_cfs": round(interval.mean_value, 6),
            }
        )

    gaps_with_stage = [row for row in gap_rows if row["stage_continued"]]
    longest_gap = max(gap_rows, key=lambda row: float(row["gap_hours_between_observations"]), default=None)
    longest_negative = max(
        negative_rows,
        key=lambda row: float(row["duration_hours"]),
        default=None,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    gaps_csv = output_dir / "discharge_gaps.csv"
    negative_csv = output_dir / "negative_flow_intervals.csv"
    summary_path = output_dir / "rincon_flow_summary.json"
    receipt_path = output_dir / "analysis-receipt.json"

    _atomic_write_csv(
        gaps_csv,
        [
            "previous_discharge_observed_at",
            "next_discharge_observed_at",
            "missing_start",
            "missing_end_exclusive",
            "gap_hours_between_observations",
            "missing_discharge_slots",
            "stage_records_during_missing_slots",
            "stage_coverage_ratio",
            "stage_continued",
        ],
        gap_rows,
    )
    _atomic_write_csv(
        negative_csv,
        [
            "start",
            "end",
            "duration_hours",
            "observation_count",
            "minimum_discharge_cfs",
            "mean_discharge_cfs",
        ],
        negative_rows,
    )

    terminal_stage_continued = bool(
        last_discharge
        and stage_summary["last_stage_observed_at"]
        and stage_summary["last_stage_observed_at"] > _iso_z(last_discharge)
    )

    summary: dict[str, Any] = {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "build": BUILD_NUMBER,
        "analysis": "rincon_discontinuity_directional_flow",
        "query_mode": "local_finalized_archive",
        "network_requests_made": 0,
        "site_no": site_no,
        "requested_start": start,
        "requested_end": end,
        "effective_start": effective_start,
        "effective_end_exclusive": effective_end_exclusive,
        "cadence_minutes": cadence_minutes,
        "gap_threshold_hours": gap_hours,
        "stage_continuity_ratio_threshold": stage_continuity_ratio,
        "discharge_record_count": discharge_record_count,
        "first_discharge_observed_at": _iso_z(first_discharge),
        "last_discharge_observed_at": _iso_z(last_discharge),
        "minimum_discharge_cfs": minimum_discharge,
        "maximum_discharge_cfs": maximum_discharge,
        "discharge_gap_count": len(gap_rows),
        "discharge_gaps_with_stage_continuity": len(gaps_with_stage),
        "longest_discharge_gap": longest_gap,
        "negative_flow_interval_count": len(negative_rows),
        "longest_negative_flow_interval": longest_negative,
        "terminal_stage_continued_after_discharge": terminal_stage_continued,
        **stage_summary,
    }
    atomic_write_text(summary_path, json.dumps(summary, indent=2, sort_keys=True) + "\n")

    receipt: dict[str, Any] = {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "build": BUILD_NUMBER,
        "analysis": "rincon_discontinuity_directional_flow",
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
        "discharge_gaps_csv": str(gaps_csv.resolve()),
        "discharge_gaps_csv_sha256": sha256_file(gaps_csv),
        "negative_flow_intervals_csv": str(negative_csv.resolve()),
        "negative_flow_intervals_csv_sha256": sha256_file(negative_csv),
        "discharge_record_count": discharge_record_count,
        "stage_record_count": stage_summary["stage_record_count"],
        "discharge_gap_count": len(gap_rows),
        "negative_flow_interval_count": len(negative_rows),
        "last_discharge_observed_at": _iso_z(last_discharge),
        "last_stage_observed_at": stage_summary["last_stage_observed_at"],
        "terminal_stage_continued_after_discharge": terminal_stage_continued,
    }
    atomic_write_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    receipt["receipt"] = str(receipt_path.resolve())
    return receipt
