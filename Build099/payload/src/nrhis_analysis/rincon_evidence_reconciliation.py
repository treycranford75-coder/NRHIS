"""Reconcile Rincon negative-observation runs with integrated reverse-flow intervals.

Build099 explains the intentional semantic difference between Build097's runs of
negative sampled observations and Build098's piecewise-linear negative-flow
intervals. It also emits a compact critical-evidence timeline around the 2017
material discharge gap and the May 2018 terminal discharge discontinuation.

The analysis is local-only and operates against the finalized NRHIS archive.
"""
from __future__ import annotations

import csv
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

from nrhis_analysis.rincon_reverse_flow_volume import (
    Point,
    ReverseInterval,
    _detect_material_gaps,
    _integrate_reverse_flow,
    _read_points,
)
from nrhis_analysis.usgs_history_query import (
    QueryError,
    atomic_write_text,
    load_sparse_index,
    normalize_window,
    query_history,
    sha256_file,
)

ANALYSIS_SCHEMA_VERSION = 1
BUILD_NUMBER = "099"
DISCHARGE_PARAMETER = "00060"
STAGE_PARAMETER = "00065"
DEFAULT_SITE_NO = "08211503"
DEFAULT_CADENCE_MINUTES = 15
DEFAULT_GAP_HOURS = 24.0


@dataclass
class ObservationNegativeRun:
    start: datetime
    end: datetime
    count: int
    minimum_discharge_cfs: float
    sum_discharge_cfs: float

    @property
    def duration_hours(self) -> float:
        return (self.end - self.start).total_seconds() / 3600.0

    @property
    def mean_discharge_cfs(self) -> float:
        return self.sum_discharge_cfs / self.count


def _parse_observed_at(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso_z(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


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


def _observation_negative_runs(
    points: Iterable[Point], *, cadence: timedelta
) -> list[ObservationNegativeRun]:
    """Replicate Build097 negative-observation run semantics exactly."""
    runs: list[ObservationNegativeRun] = []
    active: ObservationNegativeRun | None = None
    previous_time: datetime | None = None
    for point in points:
        if previous_time is not None and point.observed_at - previous_time > cadence * 2:
            if active is not None:
                runs.append(active)
                active = None
        if point.value < 0:
            if active is None:
                active = ObservationNegativeRun(
                    start=point.observed_at,
                    end=point.observed_at,
                    count=1,
                    minimum_discharge_cfs=point.value,
                    sum_discharge_cfs=point.value,
                )
            else:
                active.end = point.observed_at
                active.count += 1
                active.minimum_discharge_cfs = min(active.minimum_discharge_cfs, point.value)
                active.sum_discharge_cfs += point.value
        elif active is not None:
            runs.append(active)
            active = None
        previous_time = point.observed_at
    if active is not None:
        runs.append(active)
    return runs


def _exact_zero_bridges(points: list[Point], *, cadence: timedelta) -> list[dict[str, Any]]:
    """Find single exact-zero samples that join negative runs under linear integration."""
    result: list[dict[str, Any]] = []
    max_delta = cadence * 2
    for previous, zero, current in zip(points, points[1:], points[2:]):
        if (
            previous.value < 0
            and zero.value == 0
            and current.value < 0
            and zero.observed_at - previous.observed_at <= max_delta
            and current.observed_at - zero.observed_at <= max_delta
        ):
            result.append(
                {
                    "previous_negative_at": _iso_z(previous.observed_at),
                    "zero_at": _iso_z(zero.observed_at),
                    "next_negative_at": _iso_z(current.observed_at),
                    "previous_discharge_cfs": previous.value,
                    "next_discharge_cfs": current.value,
                }
            )
    return result


def _overlaps_observation_run(
    interval: ReverseInterval,
    run: ObservationNegativeRun,
    *,
    tolerance_seconds: float = 1.0,
) -> bool:
    tolerance = timedelta(seconds=tolerance_seconds)
    return run.end >= interval.start - tolerance and run.start <= interval.end + tolerance


def _reconcile(
    observation_runs: list[ObservationNegativeRun],
    integrated_intervals: list[ReverseInterval],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    mapped_run_ids: set[int] = set()
    rows: list[dict[str, Any]] = []
    merged_excess = 0
    for interval_id, interval in enumerate(integrated_intervals, start=1):
        ids = [
            run_id
            for run_id, run in enumerate(observation_runs, start=1)
            if _overlaps_observation_run(interval, run)
        ]
        mapped_run_ids.update(ids)
        excess = max(0, len(ids) - 1)
        merged_excess += excess
        rows.append(
            {
                "integrated_interval_id": interval_id,
                "start": _iso_z(interval.start),
                "end": _iso_z(interval.end),
                "duration_hours": round(interval.duration_hours, 6),
                "segment_count": interval.segment_count,
                "minimum_discharge_cfs": round(interval.minimum_discharge_cfs, 6),
                "mean_reverse_discharge_cfs": round(interval.mean_reverse_discharge_cfs, 6),
                "reverse_volume_acft": round(interval.reverse_volume_acft, 6),
                "observation_run_count": len(ids),
                "observation_run_ids": ";".join(str(value) for value in ids),
                "merged_observation_run_excess": excess,
            }
        )
    orphan_rows: list[dict[str, Any]] = []
    for run_id, run in enumerate(observation_runs, start=1):
        if run_id in mapped_run_ids:
            continue
        orphan_rows.append(
            {
                "observation_run_id": run_id,
                "start": _iso_z(run.start),
                "end": _iso_z(run.end),
                "duration_hours": round(run.duration_hours, 6),
                "observation_count": run.count,
                "minimum_discharge_cfs": round(run.minimum_discharge_cfs, 6),
                "mean_discharge_cfs": round(run.mean_discharge_cfs, 6),
                "reason": "no_integrable_adjacent_segment_within_gap_limit",
            }
        )
    return rows, orphan_rows, merged_excess


def _atomic_write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _stage_times(
    csv_path: Path,
    index_path: Path,
    *,
    start: str,
    end: str,
    site_no: str,
) -> list[datetime]:
    return [
        _parse_observed_at(row["observed_at"])
        for row in _iter_parameter(
            csv_path,
            index_path,
            start=start,
            end=end,
            site_no=site_no,
            parameter_code=STAGE_PARAMETER,
        )
    ]


def _critical_timeline(
    *,
    points: list[Point],
    intervals: list[ReverseInterval],
    gaps: list[dict[str, Any]],
    stage_times: list[datetime],
    cadence: timedelta,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    longest_gap = max(gaps, key=lambda item: item["gap_hours"], default=None)
    last_discharge = points[-1] if points else None
    rows: list[dict[str, Any]] = []
    critical: dict[str, Any] = {}

    if longest_gap is not None:
        gap_previous = longest_gap["previous_observed_at"]
        gap_next = longest_gap["next_observed_at"]
        pre_gap = next(
            (
                interval
                for interval in intervals
                if abs((interval.end - gap_previous).total_seconds()) <= 1.0
            ),
            None,
        )
        post_gap = next((interval for interval in intervals if interval.end >= gap_next), None)
        missing_start = longest_gap["missing_start"]
        missing_end = longest_gap["missing_end_exclusive"]
        stage_in_gap = sum(1 for value in stage_times if missing_start <= value < missing_end)
        missing_slots = int(longest_gap["missing_slots"])
        coverage = min(1.0, stage_in_gap / missing_slots) if missing_slots else 0.0

        if pre_gap is not None:
            row = {
                "event": "reverse_interval_ending_at_gap",
                "start": _iso_z(pre_gap.start),
                "end": _iso_z(pre_gap.end),
                "status": "observable",
                "duration_hours": round(pre_gap.duration_hours, 6),
                "reverse_volume_acft": round(pre_gap.reverse_volume_acft, 6),
                "mean_reverse_discharge_cfs": round(pre_gap.mean_reverse_discharge_cfs, 6),
                "minimum_discharge_cfs": round(pre_gap.minimum_discharge_cfs, 6),
                "stage_records": "",
                "stage_coverage_ratio": "",
            }
            rows.append(row)
            critical["reverse_interval_ending_at_gap"] = row

        gap_row = {
            "event": "material_discharge_gap",
            "start": _iso_z(missing_start),
            "end": _iso_z(missing_end),
            "status": "not_observable_from_discharge",
            "duration_hours": round(float(longest_gap["gap_hours"]), 6),
            "reverse_volume_acft": "",
            "mean_reverse_discharge_cfs": "",
            "minimum_discharge_cfs": "",
            "stage_records": stage_in_gap,
            "stage_coverage_ratio": round(coverage, 6),
        }
        rows.append(gap_row)
        critical["material_discharge_gap"] = gap_row

        if post_gap is not None:
            row = {
                "event": "first_reverse_interval_after_gap",
                "start": _iso_z(post_gap.start),
                "end": _iso_z(post_gap.end),
                "status": "observable",
                "duration_hours": round(post_gap.duration_hours, 6),
                "reverse_volume_acft": round(post_gap.reverse_volume_acft, 6),
                "mean_reverse_discharge_cfs": round(post_gap.mean_reverse_discharge_cfs, 6),
                "minimum_discharge_cfs": round(post_gap.minimum_discharge_cfs, 6),
                "stage_records": "",
                "stage_coverage_ratio": "",
            }
            rows.append(row)
            critical["first_reverse_interval_after_gap"] = row

    if last_discharge is not None:
        post_terminal_start = last_discharge.observed_at + cadence
        stage_after = [value for value in stage_times if value > last_discharge.observed_at]
        row = {
            "event": "terminal_discharge_discontinuation",
            "start": _iso_z(last_discharge.observed_at),
            "end": _iso_z(stage_times[-1]) if stage_times else "",
            "status": "discharge_not_observable_after_terminal",
            "duration_hours": "",
            "reverse_volume_acft": "",
            "mean_reverse_discharge_cfs": last_discharge.value,
            "minimum_discharge_cfs": "",
            "stage_records": len(stage_after),
            "stage_coverage_ratio": "",
        }
        rows.append(row)
        critical["terminal_discharge"] = {
            **row,
            "first_stage_after_terminal": _iso_z(stage_after[0]) if stage_after else None,
            "post_terminal_start": _iso_z(post_terminal_start),
        }
    return rows, critical


def analyze_rincon_evidence_reconciliation(
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
    if cadence_minutes < 1:
        raise QueryError("cadence_minutes must be at least 1")
    if gap_hours <= 0:
        raise QueryError("gap_hours must be greater than 0")

    index = load_sparse_index(index_path, csv_path)
    effective_start, effective_end = normalize_window(start, end)
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
    observation_runs = _observation_negative_runs(points, cadence=cadence)
    integrated_intervals, _ = _integrate_reverse_flow(points, cadence=cadence)
    gaps = _detect_material_gaps(points, cadence=cadence, gap_hours=gap_hours)
    zero_bridges = _exact_zero_bridges(points, cadence=cadence)
    reconciliation_rows, orphan_rows, merged_excess = _reconcile(
        observation_runs, integrated_intervals
    )
    stage_times = _stage_times(
        csv_path,
        index_path,
        start=start,
        end=end,
        site_no=site_no,
    )
    timeline_rows, critical = _critical_timeline(
        points=points,
        intervals=integrated_intervals,
        gaps=gaps,
        stage_times=stage_times,
        cadence=cadence,
    )

    observed_count = len(observation_runs)
    integrated_count = len(integrated_intervals)
    difference = observed_count - integrated_count
    orphan_count = len(orphan_rows)
    identity_rhs = integrated_count + merged_excess + orphan_count
    identity_holds = observed_count == identity_rhs
    sustained_6h = [item for item in integrated_intervals if item.duration_hours >= 6]
    sustained_24h = [item for item in integrated_intervals if item.duration_hours >= 24]
    total_volume = sum(item.reverse_volume_acft for item in integrated_intervals)

    output_dir.mkdir(parents=True, exist_ok=True)
    reconciliation_csv = output_dir / "interval_reconciliation.csv"
    orphan_csv = output_dir / "unintegrated_observation_runs.csv"
    zero_csv = output_dir / "exact_zero_bridges.csv"
    timeline_csv = output_dir / "critical_timeline.csv"
    summary_path = output_dir / "rincon_evidence_reconciliation_summary.json"
    receipt_path = output_dir / "analysis-receipt.json"

    _atomic_write_csv(
        reconciliation_csv,
        [
            "integrated_interval_id",
            "start",
            "end",
            "duration_hours",
            "segment_count",
            "minimum_discharge_cfs",
            "mean_reverse_discharge_cfs",
            "reverse_volume_acft",
            "observation_run_count",
            "observation_run_ids",
            "merged_observation_run_excess",
        ],
        reconciliation_rows,
    )
    _atomic_write_csv(
        orphan_csv,
        [
            "observation_run_id",
            "start",
            "end",
            "duration_hours",
            "observation_count",
            "minimum_discharge_cfs",
            "mean_discharge_cfs",
            "reason",
        ],
        orphan_rows,
    )
    _atomic_write_csv(
        zero_csv,
        [
            "previous_negative_at",
            "zero_at",
            "next_negative_at",
            "previous_discharge_cfs",
            "next_discharge_cfs",
        ],
        zero_bridges,
    )
    _atomic_write_csv(
        timeline_csv,
        [
            "event",
            "start",
            "end",
            "status",
            "duration_hours",
            "reverse_volume_acft",
            "mean_reverse_discharge_cfs",
            "minimum_discharge_cfs",
            "stage_records",
            "stage_coverage_ratio",
        ],
        timeline_rows,
    )

    summary: dict[str, Any] = {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "build": BUILD_NUMBER,
        "analysis": "rincon_negative_interval_reconciliation",
        "query_mode": "local_finalized_archive",
        "network_requests_made": 0,
        "site_no": site_no,
        "requested_start": start,
        "requested_end": end,
        "effective_start": effective_start,
        "effective_end_exclusive": effective_end,
        "cadence_minutes": cadence_minutes,
        "gap_threshold_hours": gap_hours,
        "discharge_observation_count": len(points),
        "observation_negative_interval_count_build097_semantics": observed_count,
        "integrated_reverse_flow_interval_count_build098_semantics": integrated_count,
        "interval_count_difference": difference,
        "merged_observation_run_excess": merged_excess,
        "unintegrated_observation_run_count": orphan_count,
        "exact_zero_bridge_count": len(zero_bridges),
        "count_reconciliation_identity": (
            "observation_count = integrated_count + merged_run_excess + unintegrated_runs"
        ),
        "count_reconciliation_identity_holds": identity_holds,
        "total_reverse_flow_volume_acft": round(total_volume, 6),
        "sustained_reverse_intervals_ge_6h": len(sustained_6h),
        "sustained_reverse_volume_ge_6h_acft": round(
            sum(item.reverse_volume_acft for item in sustained_6h), 6
        ),
        "multiday_reverse_intervals_ge_24h": len(sustained_24h),
        "multiday_reverse_volume_ge_24h_acft": round(
            sum(item.reverse_volume_acft for item in sustained_24h), 6
        ),
        "critical_timeline": critical,
        "interpretation_note": (
            "Build097 counts runs of sampled values below zero. Build098 integrates the "
            "negative portion of adjacent observation pairs and joins pieces that touch at "
            "a solved zero crossing. A single exact-zero sample between negative observations "
            "therefore splits Build097 runs but can remain one Build098 integrated interval."
        ),
    }
    atomic_write_text(summary_path, json.dumps(summary, indent=2, sort_keys=True) + "\n")

    receipt: dict[str, Any] = {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "build": BUILD_NUMBER,
        "analysis": "rincon_negative_interval_reconciliation",
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
        "interval_reconciliation_csv": str(reconciliation_csv.resolve()),
        "interval_reconciliation_csv_sha256": sha256_file(reconciliation_csv),
        "unintegrated_observation_runs_csv": str(orphan_csv.resolve()),
        "unintegrated_observation_runs_csv_sha256": sha256_file(orphan_csv),
        "exact_zero_bridges_csv": str(zero_csv.resolve()),
        "exact_zero_bridges_csv_sha256": sha256_file(zero_csv),
        "critical_timeline_csv": str(timeline_csv.resolve()),
        "critical_timeline_csv_sha256": sha256_file(timeline_csv),
        "observation_negative_interval_count": observed_count,
        "integrated_reverse_flow_interval_count": integrated_count,
        "interval_count_difference": difference,
        "count_reconciliation_identity_holds": identity_holds,
        "total_reverse_flow_volume_acft": round(total_volume, 6),
    }
    atomic_write_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    receipt["receipt"] = str(receipt_path.resolve())
    return receipt
