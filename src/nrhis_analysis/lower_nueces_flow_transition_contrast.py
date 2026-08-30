"""Build104 lower Nueces upper-flow transition contrast analysis.

Build103 showed that a cumulative exceedance scan can report coherence at the
0th percentile when a small number of large hydrographs dominate covariance.
That is useful aggregate information but it is not a defensible event threshold.

Build104 corrects that specific issue by comparing disjoint lower-flow and
upper-flow subsets at each candidate percentile threshold. A transition is only
reported when the upper subset is coherent, the lower subset remains weak, the
upper best lag is not on a search boundary, and coherence persists at the next
configured threshold step(s). The scan is intentionally restricted to the upper
part of the discharge distribution so the selected threshold cannot represent
nearly the entire record.

All results are descriptive. They do not establish physical travel time, a
reach water balance, or causation.
"""
from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
import csv
import json

from nrhis_analysis.lower_nueces_flow_network import (
    DEFAULT_SITE_NOS,
    DISCHARGE_PARAMETER,
    PAIR_SPECS,
)
from nrhis_analysis.lower_nueces_lag_stability import (
    _best_and_peak_windows,
    _build_hourly_values,
    _lag_surface,
)
from nrhis_analysis.lower_nueces_flow_state_transition import (
    _coherence_class,
    _detect_high_flow_events,
    _iso_z,
    _lag_surface_for_hours,
    _percentile,
    _residual_summary,
)
from nrhis_analysis.usgs_history_query import (
    QueryError,
    load_sparse_index,
    normalize_window,
    query_history,
    sha256_file,
)

BUILD_NUMBER = "104"
ANALYSIS_SCHEMA_VERSION = 1
DEFAULT_PERCENTILE_STEP = 5
DEFAULT_MIN_TRANSITION_PERCENTILE = 60
DEFAULT_MAX_TRANSITION_PERCENTILE = 90
DEFAULT_COHERENCE_R = 0.8
DEFAULT_STRONG_R = 0.9
DEFAULT_MAX_LOWER_R = 0.5
DEFAULT_CONFIRM_STEPS = 2
DEFAULT_BAND_WIDTH_PERCENTILE = 20
DEFAULT_EVENT_GAP_TOLERANCE_HOURS = 2
DEFAULT_MIN_EVENT_HIGH_HOURS = 12
DEFAULT_EVENT_MIN_PAIRED_HOURS = 6


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


def _r_value(peak: dict[str, Any]) -> float | None:
    value = peak.get("best_pearson_r", "")
    if value == "" or value is None:
        return None
    return float(value)


def _is_boundary_lag(peak: dict[str, Any], max_lag_hours: int) -> bool:
    lag = peak.get("best_lag_hours", "")
    return lag != "" and int(lag) in (0, max_lag_hours)


def _split_threshold_scan(
    upstream_values: dict[datetime, float],
    downstream_values: dict[datetime, float],
    *,
    pair: str,
    max_lag_hours: int,
    min_paired_hours: int,
    percentile_step: int,
    min_transition_percentile: int,
    max_transition_percentile: int,
    coherence_r: float,
    strong_r: float,
) -> list[dict[str, Any]]:
    """Compare lower and upper disjoint subsets at candidate thresholds."""
    if percentile_step < 1 or percentile_step > 25:
        raise QueryError("percentile_step must be between 1 and 25")
    if not 1 <= min_transition_percentile < max_transition_percentile <= 99:
        raise QueryError(
            "Require 1 <= min_transition_percentile < max_transition_percentile <= 99"
        )

    values = list(upstream_values.values())
    total_hours = len(values)
    rows: list[dict[str, Any]] = []
    for percentile in range(
        min_transition_percentile,
        max_transition_percentile + 1,
        percentile_step,
    ):
        threshold = _percentile(values, float(percentile))
        lower_surface = _lag_surface(
            upstream_values,
            downstream_values,
            max_lag_hours=max_lag_hours,
            min_paired_hours=min_paired_hours,
            upstream_filter=lambda value, cut=threshold: value < cut,
        )
        upper_surface = _lag_surface(
            upstream_values,
            downstream_values,
            max_lag_hours=max_lag_hours,
            min_paired_hours=min_paired_hours,
            upstream_filter=lambda value, cut=threshold: value >= cut,
        )
        lower_peak = _best_and_peak_windows(lower_surface)
        upper_peak = _best_and_peak_windows(upper_surface)
        lower_r = _r_value(lower_peak)
        upper_r = _r_value(upper_peak)
        lower_hours = sum(1 for value in values if value < threshold)
        upper_hours = sum(1 for value in values if value >= threshold)
        rows.append(
            {
                "pair": pair,
                "threshold_percentile": percentile,
                "threshold_cfs": round(threshold, 6),
                "lower_upstream_hours": lower_hours,
                "upper_upstream_hours": upper_hours,
                "upper_fraction": round(upper_hours / total_hours, 6)
                if total_hours
                else "",
                "lower_best_lag_hours": lower_peak["best_lag_hours"],
                "lower_best_pearson_r": lower_peak["best_pearson_r"],
                "lower_best_paired_hours": lower_peak["best_paired_hours"],
                "lower_boundary_lag": _is_boundary_lag(lower_peak, max_lag_hours),
                "lower_coherence_class": _coherence_class(
                    lower_peak["best_pearson_r"],
                    coherence_r=coherence_r,
                    strong_r=strong_r,
                ),
                "upper_best_lag_hours": upper_peak["best_lag_hours"],
                "upper_best_pearson_r": upper_peak["best_pearson_r"],
                "upper_best_paired_hours": upper_peak["best_paired_hours"],
                "upper_lag_min_delta0005": upper_peak["lag_min_delta0005"],
                "upper_lag_max_delta0005": upper_peak["lag_max_delta0005"],
                "upper_lag_min_delta001": upper_peak["lag_min_delta001"],
                "upper_lag_max_delta001": upper_peak["lag_max_delta001"],
                "upper_boundary_lag": _is_boundary_lag(upper_peak, max_lag_hours),
                "upper_coherence_class": _coherence_class(
                    upper_peak["best_pearson_r"],
                    coherence_r=coherence_r,
                    strong_r=strong_r,
                ),
                "pearson_r_contrast": round(upper_r - lower_r, 8)
                if upper_r is not None and lower_r is not None
                else "",
                "status": "descriptive_split_threshold",
            }
        )
    return rows


def _find_upper_flow_transition(
    rows: list[dict[str, Any]],
    *,
    coherence_r: float,
    max_lower_r: float,
    confirm_steps: int,
) -> dict[str, Any] | None:
    """Find the earliest upper-flow threshold with persistent contrast."""
    if confirm_steps < 1:
        raise QueryError("confirm_steps must be at least 1")
    ordered = sorted(rows, key=lambda row: int(row["threshold_percentile"]))
    for index in range(0, len(ordered) - confirm_steps + 1):
        current = ordered[index]
        lower_r = current["lower_best_pearson_r"]
        if lower_r == "" or float(lower_r) > max_lower_r:
            continue
        window = ordered[index : index + confirm_steps]
        if not all(
            row["upper_best_pearson_r"] != ""
            and float(row["upper_best_pearson_r"]) >= coherence_r
            and not bool(row["upper_boundary_lag"])
            for row in window
        ):
            continue
        result = dict(current)
        result["confirmation_steps"] = confirm_steps
        result["confirmed_through_percentile"] = int(
            window[-1]["threshold_percentile"]
        )
        result["max_lower_r_required"] = max_lower_r
        return result
    return None


def _flow_band_scan(
    upstream_values: dict[datetime, float],
    downstream_values: dict[datetime, float],
    *,
    pair: str,
    max_lag_hours: int,
    min_paired_hours: int,
    band_width_percentile: int,
    coherence_r: float,
    strong_r: float,
) -> list[dict[str, Any]]:
    """Measure lag coherence in non-overlapping percentile bands."""
    if band_width_percentile < 5 or 100 % band_width_percentile != 0:
        raise QueryError("band_width_percentile must divide 100 and be at least 5")
    values = list(upstream_values.values())
    rows: list[dict[str, Any]] = []
    for low_p in range(0, 100, band_width_percentile):
        high_p = low_p + band_width_percentile
        low_cut = _percentile(values, float(low_p))
        high_cut = _percentile(values, float(high_p))
        inclusive_high = high_p == 100

        def predicate(
            value: float,
            lo: float = low_cut,
            hi: float = high_cut,
            include_hi: bool = inclusive_high,
        ) -> bool:
            if include_hi:
                return lo <= value <= hi
            return lo <= value < hi
        surface = _lag_surface(
            upstream_values,
            downstream_values,
            max_lag_hours=max_lag_hours,
            min_paired_hours=min_paired_hours,
            upstream_filter=predicate,
        )
        peak = _best_and_peak_windows(surface)
        rows.append(
            {
                "pair": pair,
                "band_percentile_low": low_p,
                "band_percentile_high": high_p,
                "band_cfs_low": round(low_cut, 6),
                "band_cfs_high": round(high_cut, 6),
                "band_upstream_hours": sum(
                    1 for value in values if predicate(value)
                ),
                **peak,
                "boundary_lag": _is_boundary_lag(peak, max_lag_hours),
                "coherence_class": _coherence_class(
                    peak["best_pearson_r"],
                    coherence_r=coherence_r,
                    strong_r=strong_r,
                ),
                "status": "descriptive_nonoverlapping_flow_band",
            }
        )
    return rows


def analyze_lower_nueces_flow_transition_contrast(
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
    min_transition_percentile: int = DEFAULT_MIN_TRANSITION_PERCENTILE,
    max_transition_percentile: int = DEFAULT_MAX_TRANSITION_PERCENTILE,
    coherence_r: float = DEFAULT_COHERENCE_R,
    strong_r: float = DEFAULT_STRONG_R,
    max_lower_r: float = DEFAULT_MAX_LOWER_R,
    confirm_steps: int = DEFAULT_CONFIRM_STEPS,
    band_width_percentile: int = DEFAULT_BAND_WIDTH_PERCENTILE,
    event_gap_tolerance_hours: int = DEFAULT_EVENT_GAP_TOLERANCE_HOURS,
    min_event_high_hours: int = DEFAULT_MIN_EVENT_HIGH_HOURS,
    event_min_paired_hours: int = DEFAULT_EVENT_MIN_PAIRED_HOURS,
) -> dict[str, Any]:
    if not 0 < max_lower_r < coherence_r <= strong_r <= 1:
        raise QueryError("Require 0 < max_lower_r < coherence_r <= strong_r <= 1")
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

    split_rows: list[dict[str, Any]] = []
    transition_rows: list[dict[str, Any]] = []
    band_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    residual_rows: list[dict[str, Any]] = []

    for pair_name, upstream, downstream in PAIR_SPECS:
        pair_split = _split_threshold_scan(
            hourly[upstream],
            hourly[downstream],
            pair=pair_name,
            max_lag_hours=max_lag_hours,
            min_paired_hours=min_paired_hours,
            percentile_step=percentile_step,
            min_transition_percentile=min_transition_percentile,
            max_transition_percentile=max_transition_percentile,
            coherence_r=coherence_r,
            strong_r=strong_r,
        )
        split_rows.extend(pair_split)
        band_rows.extend(
            _flow_band_scan(
                hourly[upstream],
                hourly[downstream],
                pair=pair_name,
                max_lag_hours=max_lag_hours,
                min_paired_hours=min_paired_hours,
                band_width_percentile=band_width_percentile,
                coherence_r=coherence_r,
                strong_r=strong_r,
            )
        )
        transition = _find_upper_flow_transition(
            pair_split,
            coherence_r=coherence_r,
            max_lower_r=max_lower_r,
            confirm_steps=confirm_steps,
        )
        if transition is None:
            transition_rows.append(
                {
                    "pair": pair_name,
                    "transition_found": False,
                    "threshold_percentile": "",
                    "threshold_cfs": "",
                    "lower_best_lag_hours": "",
                    "lower_best_pearson_r": "",
                    "upper_best_lag_hours": "",
                    "upper_best_pearson_r": "",
                    "upper_best_paired_hours": 0,
                    "upper_lag_min_delta0005": "",
                    "upper_lag_max_delta0005": "",
                    "upper_lag_min_delta001": "",
                    "upper_lag_max_delta001": "",
                    "pearson_r_contrast": "",
                    "confirmation_steps": confirm_steps,
                    "confirmed_through_percentile": "",
                    "status": "upper_flow_transition_not_resolved",
                }
            )
            continue

        transition_rows.append(
            {
                "pair": pair_name,
                "transition_found": True,
                "threshold_percentile": transition["threshold_percentile"],
                "threshold_cfs": transition["threshold_cfs"],
                "lower_best_lag_hours": transition["lower_best_lag_hours"],
                "lower_best_pearson_r": transition["lower_best_pearson_r"],
                "upper_best_lag_hours": transition["upper_best_lag_hours"],
                "upper_best_pearson_r": transition["upper_best_pearson_r"],
                "upper_best_paired_hours": transition["upper_best_paired_hours"],
                "upper_lag_min_delta0005": transition["upper_lag_min_delta0005"],
                "upper_lag_max_delta0005": transition["upper_lag_max_delta0005"],
                "upper_lag_min_delta001": transition["upper_lag_min_delta001"],
                "upper_lag_max_delta001": transition["upper_lag_max_delta001"],
                "pearson_r_contrast": transition["pearson_r_contrast"],
                "confirmation_steps": transition["confirmation_steps"],
                "confirmed_through_percentile": transition[
                    "confirmed_through_percentile"
                ],
                "status": "upper_flow_transition_contrast_descriptive",
            }
        )

        threshold = float(transition["threshold_cfs"])
        lag = int(transition["upper_best_lag_hours"])
        residual_rows.append(
            {
                "pair": pair_name,
                "threshold_percentile": transition["threshold_percentile"],
                "threshold_cfs": transition["threshold_cfs"],
                "lag_hours": lag,
                "upper_correlation_at_threshold": transition[
                    "upper_best_pearson_r"
                ],
                "lower_correlation_below_threshold": transition[
                    "lower_best_pearson_r"
                ],
                **_residual_summary(
                    hourly[upstream],
                    hourly[downstream],
                    threshold=threshold,
                    lag_hours=lag,
                ),
                "status": "upper_flow_residual_not_water_balance",
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
            event_rows.append(
                {
                    "pair": pair_name,
                    "event_id": f"{pair_name}-{event_index:03d}",
                    "threshold_percentile": transition["threshold_percentile"],
                    "threshold_cfs": round(threshold, 6),
                    "event_start": _iso_z(event["event_start"]),
                    "event_end_exclusive": _iso_z(event["event_end_exclusive"]),
                    "high_hours": event["high_hours"],
                    "span_hours": round(float(event["span_hours"]), 6),
                    "upstream_mean_cfs": round(float(event["upstream_mean_cfs"]), 6),
                    "upstream_max_cfs": round(float(event["upstream_max_cfs"]), 6),
                    **peak,
                    "boundary_lag": _is_boundary_lag(peak, max_lag_hours),
                    "coherence_class": _coherence_class(
                        peak["best_pearson_r"],
                        coherence_r=coherence_r,
                        strong_r=strong_r,
                    ),
                    "status": "descriptive_upper_flow_event_alignment",
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    split_path = output_dir / "upper_lower_threshold_contrast.csv"
    transition_path = output_dir / "upper_flow_transition.csv"
    band_path = output_dir / "nonoverlapping_flow_band_coherence.csv"
    event_path = output_dir / "upper_flow_event_lags.csv"
    residual_path = output_dir / "upper_flow_residual_summary.csv"
    summary_path = output_dir / "lower_nueces_flow_transition_contrast_summary.json"
    receipt_path = output_dir / "analysis-receipt.json"

    _atomic_write_csv(
        split_path,
        [
            "pair",
            "threshold_percentile",
            "threshold_cfs",
            "lower_upstream_hours",
            "upper_upstream_hours",
            "upper_fraction",
            "lower_best_lag_hours",
            "lower_best_pearson_r",
            "lower_best_paired_hours",
            "lower_boundary_lag",
            "lower_coherence_class",
            "upper_best_lag_hours",
            "upper_best_pearson_r",
            "upper_best_paired_hours",
            "upper_lag_min_delta0005",
            "upper_lag_max_delta0005",
            "upper_lag_min_delta001",
            "upper_lag_max_delta001",
            "upper_boundary_lag",
            "upper_coherence_class",
            "pearson_r_contrast",
            "status",
        ],
        split_rows,
    )
    _atomic_write_csv(
        transition_path,
        [
            "pair",
            "transition_found",
            "threshold_percentile",
            "threshold_cfs",
            "lower_best_lag_hours",
            "lower_best_pearson_r",
            "upper_best_lag_hours",
            "upper_best_pearson_r",
            "upper_best_paired_hours",
            "upper_lag_min_delta0005",
            "upper_lag_max_delta0005",
            "upper_lag_min_delta001",
            "upper_lag_max_delta001",
            "pearson_r_contrast",
            "confirmation_steps",
            "confirmed_through_percentile",
            "status",
        ],
        transition_rows,
    )
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
        band_path,
        [
            "pair",
            "band_percentile_low",
            "band_percentile_high",
            "band_cfs_low",
            "band_cfs_high",
            "band_upstream_hours",
            *peak_fields,
            "boundary_lag",
            "coherence_class",
            "status",
        ],
        band_rows,
    )
    _atomic_write_csv(
        event_path,
        [
            "pair",
            "event_id",
            "threshold_percentile",
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
            "upper_correlation_at_threshold",
            "lower_correlation_below_threshold",
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
        "analysis": "lower_nueces_upper_flow_transition_contrast",
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
        "min_transition_percentile": min_transition_percentile,
        "max_transition_percentile": max_transition_percentile,
        "coherence_r_threshold": coherence_r,
        "strong_r_threshold": strong_r,
        "max_lower_r_for_transition": max_lower_r,
        "transition_confirmation_steps": confirm_steps,
        "band_width_percentile": band_width_percentile,
        "event_gap_tolerance_hours": event_gap_tolerance_hours,
        "min_event_high_hours": min_event_high_hours,
        "event_min_paired_hours": event_min_paired_hours,
        "upper_flow_transition": transition_rows,
        "split_threshold_row_count": len(split_rows),
        "flow_band_row_count": len(band_rows),
        "upper_flow_event_row_count": len(event_rows),
        "upper_flow_residual_row_count": len(residual_rows),
        "interpretation": {
            "causal_claim": False,
            "physical_travel_time_claim": False,
            "water_balance_claim": False,
            "build103_supersession": (
                "Build104 supersedes Build103 coherence_onset as an event-threshold "
                "estimator because Build103 cumulative exceedance subsets can be "
                "dominated by large hydrographs even at the 0th percentile."
            ),
            "transition_definition": (
                "A descriptive upper-flow transition requires upper-subset Pearson r "
                "at or above the configured coherence threshold, lower-subset r at or "
                "below the configured weak threshold, a non-boundary upper best lag, "
                "and persistence across consecutive upper-threshold steps."
            ),
            "limitations": [
                "The selected percentile threshold is an analytical screening boundary, not a hydrologic law or regulatory threshold.",
                "Correlation alignment is not proof of physical water-particle travel time.",
                "Residuals are downstream minus upstream discharge after a statistical lag and are not a reach water balance.",
                "Reservoir operations, diversions, tributary inflows, reach storage, local gains or losses, backwater, regulation, and measurement behavior can affect results.",
            ],
        },
        "source_csv": str(csv_path.resolve()),
        "source_csv_bytes": int(index["source_csv_bytes"]),
        "source_csv_sha256": str(index["source_csv_sha256"]),
        "query_index": str(index_path.resolve()),
        "query_index_sha256": sha256_file(index_path),
    }

    for label, path in (
        ("upper_lower_threshold_contrast_csv", split_path),
        ("upper_flow_transition_csv", transition_path),
        ("nonoverlapping_flow_band_coherence_csv", band_path),
        ("upper_flow_event_lags_csv", event_path),
        ("upper_flow_residual_summary_csv", residual_path),
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
