"""Build103 lower Nueces flow-state coherence and high-flow routing analysis.

This module operates only on the finalized local NRHIS historical archive. It
extends Build102 by determining where lag correlation becomes statistically
coherent as upstream discharge increases, then restricts event and residual
analysis to those coherent-flow conditions. Results remain descriptive and do
not establish physical travel time, a reach water balance, or causation.
"""
from __future__ import annotations

import csv
import json
import math
import os
import statistics
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from nrhis_analysis.lower_nueces_flow_network import (
    DEFAULT_SITE_NOS,
    DISCHARGE_PARAMETER,
    PAIR_SPECS,
)
from nrhis_analysis.lower_nueces_lag_stability import (
    _best_and_peak_windows,
    _build_hourly_values,
    _lag_surface,
    _quantiles,
)
from nrhis_analysis.usgs_history_query import (
    QueryError,
    load_sparse_index,
    normalize_window,
    query_history,
    sha256_file,
)

BUILD_NUMBER = "103"
ANALYSIS_SCHEMA_VERSION = 1
DEFAULT_PERCENTILE_STEP = 5
DEFAULT_COHERENCE_R = 0.8
DEFAULT_STRONG_R = 0.9
DEFAULT_CONFIRM_STEPS = 3
DEFAULT_EVENT_GAP_TOLERANCE_HOURS = 2
DEFAULT_MIN_EVENT_HIGH_HOURS = 12
DEFAULT_EVENT_MIN_PAIRED_HOURS = 6


def _iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_write_csv(
    path: Path,
    fieldnames: list[str],
    rows: Iterable[dict[str, Any]],
) -> None:
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


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        raise QueryError("Cannot calculate percentile of an empty series")
    if percentile < 0 or percentile > 100:
        raise QueryError("Percentile must be between 0 and 100")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * (percentile / 100.0)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _coherence_class(r_value: float | str, *, coherence_r: float, strong_r: float) -> str:
    if r_value == "":
        return "insufficient_pairs"
    r = float(r_value)
    if r >= strong_r:
        return "strong"
    if r >= coherence_r:
        return "coherent"
    return "weak_or_unresolved"


def _threshold_scan(
    upstream_values: dict[datetime, float],
    downstream_values: dict[datetime, float],
    *,
    pair: str,
    max_lag_hours: int,
    min_paired_hours: int,
    percentile_step: int,
    coherence_r: float,
    strong_r: float,
) -> list[dict[str, Any]]:
    if percentile_step < 1 or percentile_step > 50:
        raise QueryError("percentile_step must be between 1 and 50")
    values = list(upstream_values.values())
    rows: list[dict[str, Any]] = []
    for percentile in range(0, 91, percentile_step):
        threshold = _percentile(values, float(percentile))
        surface = _lag_surface(
            upstream_values,
            downstream_values,
            max_lag_hours=max_lag_hours,
            min_paired_hours=min_paired_hours,
            upstream_filter=lambda value, cut=threshold: value >= cut,
        )
        peak = _best_and_peak_windows(surface)
        best_lag = peak["best_lag_hours"]
        boundary = best_lag != "" and int(best_lag) in (0, max_lag_hours)
        rows.append(
            {
                "pair": pair,
                "threshold_percentile": percentile,
                "threshold_cfs": round(threshold, 6),
                "upstream_hours_at_or_above": sum(
                    1 for value in upstream_values.values() if value >= threshold
                ),
                **peak,
                "boundary_lag": bool(boundary),
                "coherence_class": _coherence_class(
                    peak["best_pearson_r"],
                    coherence_r=coherence_r,
                    strong_r=strong_r,
                ),
                "status": "descriptive_only",
            }
        )
    return rows


def _find_sustained_coherence_onset(
    rows: list[dict[str, Any]],
    *,
    coherence_r: float,
    confirm_steps: int,
) -> dict[str, Any] | None:
    if confirm_steps < 1:
        raise QueryError("confirm_steps must be at least 1")
    ordered = sorted(rows, key=lambda row: int(row["threshold_percentile"]))
    for index in range(0, len(ordered) - confirm_steps + 1):
        window = ordered[index : index + confirm_steps]
        if all(
            row["best_pearson_r"] != ""
            and float(row["best_pearson_r"]) >= coherence_r
            and not bool(row["boundary_lag"])
            for row in window
        ):
            first = dict(window[0])
            first["confirmation_steps"] = confirm_steps
            first["confirmed_through_percentile"] = int(
                window[-1]["threshold_percentile"]
            )
            return first
    return None


def _detect_high_flow_events(
    upstream_values: dict[datetime, float],
    *,
    threshold: float,
    gap_tolerance_hours: int,
    min_high_hours: int,
) -> list[dict[str, Any]]:
    if gap_tolerance_hours < 0:
        raise QueryError("gap_tolerance_hours must be nonnegative")
    if min_high_hours < 1:
        raise QueryError("min_high_hours must be at least 1")
    high_hours = sorted(
        hour for hour, value in upstream_values.items() if value >= threshold
    )
    if not high_hours:
        return []
    groups: list[list[datetime]] = [[high_hours[0]]]
    max_gap = timedelta(hours=gap_tolerance_hours + 1)
    for hour in high_hours[1:]:
        if hour - groups[-1][-1] <= max_gap:
            groups[-1].append(hour)
        else:
            groups.append([hour])
    events: list[dict[str, Any]] = []
    for group in groups:
        if len(group) < min_high_hours:
            continue
        values = [upstream_values[hour] for hour in group]
        events.append(
            {
                "event_start": group[0],
                "event_end_exclusive": group[-1] + timedelta(hours=1),
                "high_hours": len(group),
                "span_hours": (group[-1] - group[0]).total_seconds() / 3600.0 + 1.0,
                "upstream_mean_cfs": sum(values) / len(values),
                "upstream_max_cfs": max(values),
                "upstream_hours": group,
            }
        )
    return events


def _lag_surface_for_hours(
    upstream_values: dict[datetime, float],
    downstream_values: dict[datetime, float],
    upstream_hours: list[datetime],
    *,
    max_lag_hours: int,
    min_paired_hours: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lag in range(max_lag_hours + 1):
        xs: list[float] = []
        ys: list[float] = []
        shift = timedelta(hours=lag)
        for hour in upstream_hours:
            upstream_value = upstream_values.get(hour)
            downstream_value = downstream_values.get(hour + shift)
            if upstream_value is None or downstream_value is None:
                continue
            xs.append(upstream_value)
            ys.append(downstream_value)
        if len(xs) < min_paired_hours:
            r_value: float | None = None
        else:
            x_mean = sum(xs) / len(xs)
            y_mean = sum(ys) / len(ys)
            numerator = sum(
                (x - x_mean) * (y - y_mean)
                for x, y in zip(xs, ys, strict=True)
            )
            x_ss = sum((x - x_mean) ** 2 for x in xs)
            y_ss = sum((y - y_mean) ** 2 for y in ys)
            denominator = math.sqrt(x_ss * y_ss)
            r_value = numerator / denominator if denominator else None
        rows.append(
            {
                "lag_hours": lag,
                "paired_hours": len(xs),
                "pearson_r": r_value,
            }
        )
    return rows


def _residual_summary(
    upstream_values: dict[datetime, float],
    downstream_values: dict[datetime, float],
    *,
    threshold: float,
    lag_hours: int,
) -> dict[str, Any]:
    residuals: list[float] = []
    shift = timedelta(hours=lag_hours)
    for hour, upstream_value in upstream_values.items():
        if upstream_value < threshold:
            continue
        downstream_value = downstream_values.get(hour + shift)
        if downstream_value is None:
            continue
        residuals.append(downstream_value - upstream_value)
    if not residuals:
        return {
            "paired_hours": 0,
            "mean_residual_cfs": "",
            "median_residual_cfs": "",
            "p10_residual_cfs": "",
            "p90_residual_cfs": "",
            "fraction_positive": "",
        }
    ordered = sorted(residuals)
    n = len(ordered)
    return {
        "paired_hours": n,
        "mean_residual_cfs": round(sum(residuals) / n, 6),
        "median_residual_cfs": round(float(statistics.median(residuals)), 6),
        "p10_residual_cfs": round(ordered[int(0.10 * (n - 1))], 6),
        "p90_residual_cfs": round(ordered[int(0.90 * (n - 1))], 6),
        "fraction_positive": round(sum(1 for value in residuals if value > 0) / n, 6),
    }


def analyze_lower_nueces_flow_state_transition(
    csv_path: Path,
    index_path: Path,
    output_dir: Path,
    *,
    start: str,
    end: str,
    site_nos: tuple[str, ...] = DEFAULT_SITE_NOS,
    min_observations_per_hour: int = 2,
    max_lag_hours: int = 72,
    min_paired_hours: int = 48,
    percentile_step: int = DEFAULT_PERCENTILE_STEP,
    coherence_r: float = DEFAULT_COHERENCE_R,
    strong_r: float = DEFAULT_STRONG_R,
    confirm_steps: int = DEFAULT_CONFIRM_STEPS,
    event_gap_tolerance_hours: int = DEFAULT_EVENT_GAP_TOLERANCE_HOURS,
    min_event_high_hours: int = DEFAULT_MIN_EVENT_HIGH_HOURS,
    event_min_paired_hours: int = DEFAULT_EVENT_MIN_PAIRED_HOURS,
) -> dict[str, Any]:
    if not 0 < coherence_r <= strong_r <= 1:
        raise QueryError("Require 0 < coherence_r <= strong_r <= 1")
    if min_paired_hours < 2 or event_min_paired_hours < 2:
        raise QueryError("paired-hour requirements must be at least 2")

    index = load_sparse_index(index_path, csv_path)
    effective_start, effective_end_exclusive = normalize_window(start, end)
    rows = query_history(
        csv_path,
        index_path,
        start=start,
        end=end,
        site_nos=list(site_nos),
        parameter_codes=[DISCHARGE_PARAMETER],
    )
    hourly, coverage = _build_hourly_values(
        rows,
        site_nos=site_nos,
        min_observations_per_hour=min_observations_per_hour,
    )

    threshold_rows: list[dict[str, Any]] = []
    onset_rows: list[dict[str, Any]] = []
    tercile_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    residual_rows: list[dict[str, Any]] = []

    for pair_name, upstream, downstream in PAIR_SPECS:
        scan = _threshold_scan(
            hourly[upstream],
            hourly[downstream],
            pair=pair_name,
            max_lag_hours=max_lag_hours,
            min_paired_hours=min_paired_hours,
            percentile_step=percentile_step,
            coherence_r=coherence_r,
            strong_r=strong_r,
        )
        threshold_rows.extend(scan)
        onset = _find_sustained_coherence_onset(
            scan,
            coherence_r=coherence_r,
            confirm_steps=confirm_steps,
        )

        upstream_series = list(hourly[upstream].values())
        q1, q2 = _quantiles(upstream_series)
        for regime_name, predicate in (
            ("low", lambda value, q1=q1: value <= q1),
            ("medium", lambda value, q1=q1, q2=q2: q1 < value <= q2),
            ("high", lambda value, q2=q2: value > q2),
        ):
            surface = _lag_surface(
                hourly[upstream],
                hourly[downstream],
                max_lag_hours=max_lag_hours,
                min_paired_hours=min_paired_hours,
                upstream_filter=predicate,
            )
            peak = _best_and_peak_windows(surface)
            boundary = peak["best_lag_hours"] != "" and int(
                peak["best_lag_hours"]
            ) in (0, max_lag_hours)
            tercile_rows.append(
                {
                    "pair": pair_name,
                    "regime": regime_name,
                    "upstream_tercile_low_cut_cfs": round(q1, 6),
                    "upstream_tercile_high_cut_cfs": round(q2, 6),
                    **peak,
                    "boundary_lag": bool(boundary),
                    "coherence_class": _coherence_class(
                        peak["best_pearson_r"],
                        coherence_r=coherence_r,
                        strong_r=strong_r,
                    ),
                    "status": "descriptive_only",
                }
            )

        if onset is None:
            onset_rows.append(
                {
                    "pair": pair_name,
                    "onset_found": False,
                    "threshold_percentile": "",
                    "threshold_cfs": "",
                    "best_lag_hours": "",
                    "best_pearson_r": "",
                    "best_paired_hours": 0,
                    "confirmation_steps": confirm_steps,
                    "confirmed_through_percentile": "",
                    "status": "coherence_onset_not_resolved",
                }
            )
            continue

        onset_rows.append(
            {
                "pair": pair_name,
                "onset_found": True,
                "threshold_percentile": onset["threshold_percentile"],
                "threshold_cfs": onset["threshold_cfs"],
                "best_lag_hours": onset["best_lag_hours"],
                "best_pearson_r": onset["best_pearson_r"],
                "best_paired_hours": onset["best_paired_hours"],
                "confirmation_steps": onset["confirmation_steps"],
                "confirmed_through_percentile": onset[
                    "confirmed_through_percentile"
                ],
                "status": "sustained_coherence_onset_descriptive",
            }
        )

        threshold = float(onset["threshold_cfs"])
        lag = int(onset["best_lag_hours"])
        residual_rows.append(
            {
                "pair": pair_name,
                "threshold_percentile": onset["threshold_percentile"],
                "threshold_cfs": onset["threshold_cfs"],
                "lag_hours": lag,
                "correlation_at_threshold": onset["best_pearson_r"],
                **_residual_summary(
                    hourly[upstream],
                    hourly[downstream],
                    threshold=threshold,
                    lag_hours=lag,
                ),
                "status": "coherent_flow_residual_not_water_balance",
            }
        )

        events = _detect_high_flow_events(
            hourly[upstream],
            threshold=threshold,
            gap_tolerance_hours=event_gap_tolerance_hours,
            min_high_hours=min_event_high_hours,
        )
        for event_index, event in enumerate(events, start=1):
            surface = _lag_surface_for_hours(
                hourly[upstream],
                hourly[downstream],
                event["upstream_hours"],
                max_lag_hours=max_lag_hours,
                min_paired_hours=event_min_paired_hours,
            )
            peak = _best_and_peak_windows(surface)
            boundary = peak["best_lag_hours"] != "" and int(
                peak["best_lag_hours"]
            ) in (0, max_lag_hours)
            event_rows.append(
                {
                    "pair": pair_name,
                    "event_id": f"{pair_name}-{event_index:03d}",
                    "threshold_cfs": round(threshold, 6),
                    "event_start": _iso_z(event["event_start"]),
                    "event_end_exclusive": _iso_z(event["event_end_exclusive"]),
                    "high_hours": event["high_hours"],
                    "span_hours": round(float(event["span_hours"]), 6),
                    "upstream_mean_cfs": round(float(event["upstream_mean_cfs"]), 6),
                    "upstream_max_cfs": round(float(event["upstream_max_cfs"]), 6),
                    **peak,
                    "boundary_lag": bool(boundary),
                    "coherence_class": _coherence_class(
                        peak["best_pearson_r"],
                        coherence_r=coherence_r,
                        strong_r=strong_r,
                    ),
                    "status": "descriptive_event_alignment",
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    threshold_path = output_dir / "coherence_threshold_scan.csv"
    onset_path = output_dir / "coherence_onset.csv"
    tercile_path = output_dir / "tercile_regime_coherence.csv"
    event_path = output_dir / "coherent_flow_event_lags.csv"
    residual_path = output_dir / "coherent_flow_residual_summary.csv"
    summary_path = output_dir / "lower_nueces_flow_state_transition_summary.json"
    receipt_path = output_dir / "analysis-receipt.json"

    peak_fields = [
        "best_lag_hours",
        "best_pearson_r",
        "best_paired_hours",
        "lag_min_delta0005",
        "lag_max_delta0005",
        "lag_min_delta001",
        "lag_max_delta001",
    ]
    _atomic_write_csv(
        threshold_path,
        [
            "pair",
            "threshold_percentile",
            "threshold_cfs",
            "upstream_hours_at_or_above",
            *peak_fields,
            "boundary_lag",
            "coherence_class",
            "status",
        ],
        threshold_rows,
    )
    _atomic_write_csv(
        onset_path,
        [
            "pair",
            "onset_found",
            "threshold_percentile",
            "threshold_cfs",
            "best_lag_hours",
            "best_pearson_r",
            "best_paired_hours",
            "confirmation_steps",
            "confirmed_through_percentile",
            "status",
        ],
        onset_rows,
    )
    _atomic_write_csv(
        tercile_path,
        [
            "pair",
            "regime",
            "upstream_tercile_low_cut_cfs",
            "upstream_tercile_high_cut_cfs",
            *peak_fields,
            "boundary_lag",
            "coherence_class",
            "status",
        ],
        tercile_rows,
    )
    _atomic_write_csv(
        event_path,
        [
            "pair",
            "event_id",
            "threshold_cfs",
            "event_start",
            "event_end_exclusive",
            "high_hours",
            "span_hours",
            "upstream_mean_cfs",
            "upstream_max_cfs",
            *peak_fields,
            "boundary_lag",
            "coherence_class",
            "status",
        ],
        event_rows,
    )
    _atomic_write_csv(
        residual_path,
        [
            "pair",
            "threshold_percentile",
            "threshold_cfs",
            "lag_hours",
            "correlation_at_threshold",
            "paired_hours",
            "mean_residual_cfs",
            "median_residual_cfs",
            "p10_residual_cfs",
            "p90_residual_cfs",
            "fraction_positive",
            "status",
        ],
        residual_rows,
    )

    summary: dict[str, Any] = {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "build": BUILD_NUMBER,
        "analysis": "lower_nueces_flow_state_coherence_and_high_flow_routing",
        "created_at": _iso_z(datetime.now(timezone.utc)),
        "query_mode": "local_finalized_archive",
        "network_requests_made": 0,
        "requested_start": start,
        "requested_end": end,
        "effective_start": effective_start,
        "effective_end_exclusive": effective_end_exclusive,
        "parameter_code": DISCHARGE_PARAMETER,
        "site_nos": list(site_nos),
        "station_coverage": coverage,
        "max_lag_hours": max_lag_hours,
        "min_paired_hours": min_paired_hours,
        "percentile_step": percentile_step,
        "coherence_r_threshold": coherence_r,
        "strong_r_threshold": strong_r,
        "coherence_confirmation_steps": confirm_steps,
        "event_gap_tolerance_hours": event_gap_tolerance_hours,
        "min_event_high_hours": min_event_high_hours,
        "event_min_paired_hours": event_min_paired_hours,
        "coherence_onset": onset_rows,
        "threshold_scan_row_count": len(threshold_rows),
        "tercile_regime_row_count": len(tercile_rows),
        "coherent_flow_event_row_count": len(event_rows),
        "coherent_flow_residual_row_count": len(residual_rows),
        "interpretation": {
            "causal_claim": False,
            "physical_travel_time_claim": False,
            "water_balance_claim": False,
            "coherence_definition": (
                "Pearson r at or above the configured threshold with a best lag not "
                "at 0 or the maximum search boundary; onset requires consecutive "
                "threshold-scan confirmations"
            ),
            "limitations": [
                (
                    "Threshold coherence is descriptive statistical evidence, not proof "
                    "of physical water-particle travel time."
                ),
                (
                    "Weak low- or medium-flow correlations mean lag is unresolved; the "
                    "winning optimizer lag must not be interpreted as routing time."
                ),
                (
                    "Coherent-flow residuals are downstream minus upstream discharge "
                    "after a statistical lag and are not a reach water balance."
                ),
                (
                    "Reservoir operations, diversions, tributary inflows, reach storage, "
                    "local gains or losses, backwater, regulation, and measurement "
                    "behavior can affect results."
                ),
            ],
        },
        "source_csv": str(csv_path.resolve()),
        "source_csv_bytes": int(index["source_csv_bytes"]),
        "source_csv_sha256": str(index["source_csv_sha256"]),
        "query_index": str(index_path.resolve()),
        "query_index_sha256": sha256_file(index_path),
    }

    for label, path in (
        ("coherence_threshold_scan_csv", threshold_path),
        ("coherence_onset_csv", onset_path),
        ("tercile_regime_coherence_csv", tercile_path),
        ("coherent_flow_event_lags_csv", event_path),
        ("coherent_flow_residual_summary_csv", residual_path),
    ):
        summary[label] = str(path.resolve())
        summary[f"{label}_sha256"] = sha256_file(path)

    _atomic_write_json(summary_path, summary)
    receipt = {
        "schema_version": 1,
        "build": BUILD_NUMBER,
        "analysis": summary["analysis"],
        "created_at": _iso_z(datetime.now(timezone.utc)),
        "network_requests_made": 0,
        "source_csv_sha256": summary["source_csv_sha256"],
        "query_index_sha256": summary["query_index_sha256"],
        "summary": str(summary_path.resolve()),
        "summary_sha256": sha256_file(summary_path),
        "causation_claimed": False,
        "physical_travel_time_claimed": False,
        "water_balance_claimed": False,
    }
    _atomic_write_json(receipt_path, receipt)
    summary["receipt"] = str(receipt_path.resolve())
    summary["receipt_sha256"] = sha256_file(receipt_path)
    return summary
