"""Build102 lower Nueces lag-stability and reach-residual analysis.

This module operates only on the finalized local NRHIS historical archive. It
extends Build101 by quantifying lag-peak width, monthly/rolling lag stability,
flow-regime lag behavior, and lag-adjusted downstream-minus-upstream residuals.
All results are descriptive statistical evidence, not causal attribution, a
hydraulic routing model, or proof of water-particle travel time.
"""
from __future__ import annotations

import csv
import json
import math
import os
import statistics
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from nrhis_analysis.lower_nueces_flow_network import (
    DEFAULT_SITE_NOS,
    DISCHARGE_PARAMETER,
    PAIR_SPECS,
)
from nrhis_analysis.usgs_history_query import (
    QueryError,
    load_sparse_index,
    normalize_window,
    query_history,
    sha256_file,
)

BUILD_NUMBER = "102"
ANALYSIS_SCHEMA_VERSION = 1
PEAK_DELTAS = (0.0005, 0.001)


@dataclass
class HourAccumulator:
    count: int = 0
    total: float = 0.0

    def add(self, value: float) -> None:
        self.count += 1
        self.total += value

    @property
    def mean(self) -> float:
        return self.total / self.count


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_float(value: str) -> float | None:
    raw = str(value).strip()
    if not raw:
        return None
    try:
        parsed = float(raw)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


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


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys, strict=True))
    x_ss = sum((x - x_mean) ** 2 for x in xs)
    y_ss = sum((y - y_mean) ** 2 for y in ys)
    denominator = math.sqrt(x_ss * y_ss)
    if denominator == 0:
        return None
    return numerator / denominator


def _hour_start(value: datetime) -> datetime:
    return value.replace(minute=0, second=0, microsecond=0)


def _build_hourly_values(
    rows: Iterable[dict[str, str]],
    *,
    site_nos: tuple[str, ...],
    min_observations_per_hour: int,
) -> tuple[dict[str, dict[datetime, float]], dict[str, Any]]:
    accumulators: dict[tuple[str, datetime], HourAccumulator] = defaultdict(HourAccumulator)
    raw_counts = {site: 0 for site in site_nos}
    valid_counts = {site: 0 for site in site_nos}

    for row in rows:
        site = str(row.get("site_no", ""))
        if site not in raw_counts:
            continue
        raw_counts[site] += 1
        value = _parse_float(row.get("value", ""))
        if value is None:
            continue
        valid_counts[site] += 1
        accumulators[(site, _hour_start(_parse_time(row["observed_at"])))].add(value)

    values: dict[str, dict[datetime, float]] = {site: {} for site in site_nos}
    excluded = {site: 0 for site in site_nos}
    for (site, hour), acc in accumulators.items():
        if acc.count < min_observations_per_hour:
            excluded[site] += 1
            continue
        values[site][hour] = acc.mean

    coverage = {
        site: {
            "raw_discharge_records": raw_counts[site],
            "valid_discharge_records": valid_counts[site],
            "hourly_bins_retained": len(values[site]),
            "hourly_bins_excluded_low_count": excluded[site],
        }
        for site in site_nos
    }
    return values, coverage


def _lag_surface(
    upstream_values: dict[datetime, float],
    downstream_values: dict[datetime, float],
    *,
    max_lag_hours: int,
    min_paired_hours: int,
    window_start: datetime | None = None,
    window_end: datetime | None = None,
    upstream_filter: Any = None,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for lag in range(max_lag_hours + 1):
        xs: list[float] = []
        ys: list[float] = []
        for hour, upstream_value in upstream_values.items():
            if window_start is not None and hour < window_start:
                continue
            if window_end is not None and hour >= window_end:
                continue
            if upstream_filter is not None and not upstream_filter(upstream_value):
                continue
            downstream_hour = hour + timedelta(hours=lag)
            if window_start is not None and downstream_hour < window_start:
                continue
            if window_end is not None and downstream_hour >= window_end:
                continue
            downstream_value = downstream_values.get(downstream_hour)
            if downstream_value is None:
                continue
            xs.append(upstream_value)
            ys.append(downstream_value)
        r = _pearson(xs, ys) if len(xs) >= min_paired_hours else None
        result.append(
            {
                "lag_hours": lag,
                "paired_hours": len(xs),
                "pearson_r": r,
            }
        )
    return result


def _best_and_peak_windows(surface: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [row for row in surface if row["pearson_r"] is not None]
    if not eligible:
        return {
            "best_lag_hours": "",
            "best_pearson_r": "",
            "best_paired_hours": 0,
            "lag_min_delta0005": "",
            "lag_max_delta0005": "",
            "lag_min_delta001": "",
            "lag_max_delta001": "",
        }
    best = max(eligible, key=lambda row: float(row["pearson_r"]))
    max_r = float(best["pearson_r"])
    within_0005 = [row for row in eligible if max_r - float(row["pearson_r"]) <= 0.0005]
    within_001 = [row for row in eligible if max_r - float(row["pearson_r"]) <= 0.001]
    return {
        "best_lag_hours": int(best["lag_hours"]),
        "best_pearson_r": round(max_r, 8),
        "best_paired_hours": int(best["paired_hours"]),
        "lag_min_delta0005": min(int(row["lag_hours"]) for row in within_0005),
        "lag_max_delta0005": max(int(row["lag_hours"]) for row in within_0005),
        "lag_min_delta001": min(int(row["lag_hours"]) for row in within_001),
        "lag_max_delta001": max(int(row["lag_hours"]) for row in within_001),
    }


def _month_windows(start: datetime, end: datetime) -> list[tuple[str, datetime, datetime]]:
    cursor = datetime(start.year, start.month, 1, tzinfo=timezone.utc)
    windows: list[tuple[str, datetime, datetime]] = []
    while cursor < end:
        if cursor.month == 12:
            nxt = datetime(cursor.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            nxt = datetime(cursor.year, cursor.month + 1, 1, tzinfo=timezone.utc)
        win_start = max(cursor, start)
        win_end = min(nxt, end)
        if win_start < win_end:
            windows.append((cursor.strftime("%Y-%m"), win_start, win_end))
        cursor = nxt
    return windows


def _rolling_windows(
    start: datetime,
    end: datetime,
    *,
    window_days: int,
    step_days: int,
) -> list[tuple[datetime, datetime]]:
    result: list[tuple[datetime, datetime]] = []
    cursor = start
    span = timedelta(days=window_days)
    step = timedelta(days=step_days)
    while cursor + span <= end:
        result.append((cursor, cursor + span))
        cursor += step
    return result


def _quantiles(values: list[float]) -> tuple[float, float]:
    if len(values) < 3:
        raise QueryError("At least three upstream values are required for flow-regime analysis")
    ordered = sorted(values)
    n = len(ordered)
    q1 = ordered[int((n - 1) / 3)]
    q2 = ordered[int(2 * (n - 1) / 3)]
    return q1, q2


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def _overlap(a_min: int, a_max: int, b_min: int, b_max: int) -> tuple[bool, int | str, int | str]:
    lo = max(a_min, b_min)
    hi = min(a_max, b_max)
    return (lo <= hi, lo if lo <= hi else "", hi if lo <= hi else "")


def analyze_lower_nueces_lag_stability(
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
    rolling_days: tuple[int, ...] = (30, 60),
    rolling_step_days: int = 15,
) -> dict[str, Any]:
    if min_observations_per_hour < 1:
        raise QueryError("min_observations_per_hour must be at least 1")
    if max_lag_hours < 0:
        raise QueryError("max_lag_hours must be nonnegative")
    if min_paired_hours < 2:
        raise QueryError("min_paired_hours must be at least 2")
    if rolling_step_days < 1 or any(days < 2 for days in rolling_days):
        raise QueryError("rolling windows and step must be positive")

    index = load_sparse_index(index_path, csv_path)
    effective_start, effective_end_exclusive = normalize_window(start, end)
    start_dt = _parse_time(effective_start)
    end_dt = _parse_time(effective_end_exclusive)
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

    overall_rows: list[dict[str, Any]] = []
    monthly_rows: list[dict[str, Any]] = []
    rolling_rows: list[dict[str, Any]] = []
    regime_rows: list[dict[str, Any]] = []
    residual_rows: list[dict[str, Any]] = []
    residual_summary_rows: list[dict[str, Any]] = []
    overall_by_pair: dict[str, dict[str, Any]] = {}

    for pair_name, upstream, downstream in PAIR_SPECS:
        surface = _lag_surface(
            hourly[upstream],
            hourly[downstream],
            max_lag_hours=max_lag_hours,
            min_paired_hours=min_paired_hours,
            window_start=start_dt,
            window_end=end_dt,
        )
        peak = _best_and_peak_windows(surface)
        overall = {
            "pair": pair_name,
            "upstream_site_no": upstream,
            "downstream_site_no": downstream,
            **peak,
            "status": "descriptive_only" if peak["best_lag_hours"] != "" else "insufficient_pairs",
        }
        overall_rows.append(overall)
        overall_by_pair[pair_name] = overall

        for month, win_start, win_end in _month_windows(start_dt, end_dt):
            monthly_surface = _lag_surface(
                hourly[upstream],
                hourly[downstream],
                max_lag_hours=max_lag_hours,
                min_paired_hours=min_paired_hours,
                window_start=win_start,
                window_end=win_end,
            )
            month_peak = _best_and_peak_windows(monthly_surface)
            monthly_rows.append(
                {
                    "pair": pair_name,
                    "month": month,
                    "window_start": _iso_z(win_start),
                    "window_end_exclusive": _iso_z(win_end),
                    **month_peak,
                    "status": "descriptive_only" if month_peak["best_lag_hours"] != "" else "insufficient_pairs",
                }
            )

        for days in rolling_days:
            for win_start, win_end in _rolling_windows(
                start_dt,
                end_dt,
                window_days=days,
                step_days=rolling_step_days,
            ):
                rolling_surface = _lag_surface(
                    hourly[upstream],
                    hourly[downstream],
                    max_lag_hours=max_lag_hours,
                    min_paired_hours=min_paired_hours,
                    window_start=win_start,
                    window_end=win_end,
                )
                rolling_peak = _best_and_peak_windows(rolling_surface)
                rolling_rows.append(
                    {
                        "pair": pair_name,
                        "window_days": days,
                        "window_start": _iso_z(win_start),
                        "window_end_exclusive": _iso_z(win_end),
                        **rolling_peak,
                        "status": "descriptive_only" if rolling_peak["best_lag_hours"] != "" else "insufficient_pairs",
                    }
                )

        upstream_values = list(hourly[upstream].values())
        q1, q2 = _quantiles(upstream_values)
        regimes = (
            ("low", lambda value, q1=q1: value <= q1),
            ("medium", lambda value, q1=q1, q2=q2: q1 < value <= q2),
            ("high", lambda value, q2=q2: value > q2),
        )
        for regime_name, predicate in regimes:
            regime_surface = _lag_surface(
                hourly[upstream],
                hourly[downstream],
                max_lag_hours=max_lag_hours,
                min_paired_hours=min_paired_hours,
                window_start=start_dt,
                window_end=end_dt,
                upstream_filter=predicate,
            )
            regime_peak = _best_and_peak_windows(regime_surface)
            regime_rows.append(
                {
                    "pair": pair_name,
                    "regime": regime_name,
                    "upstream_tercile_low_cut_cfs": round(q1, 6),
                    "upstream_tercile_high_cut_cfs": round(q2, 6),
                    **regime_peak,
                    "status": "descriptive_only" if regime_peak["best_lag_hours"] != "" else "insufficient_pairs",
                }
            )

        if peak["best_lag_hours"] != "":
            lag = int(peak["best_lag_hours"])
            residuals: list[float] = []
            for upstream_hour, upstream_value in sorted(hourly[upstream].items()):
                if upstream_hour < start_dt or upstream_hour >= end_dt:
                    continue
                downstream_hour = upstream_hour + timedelta(hours=lag)
                if downstream_hour >= end_dt:
                    continue
                downstream_value = hourly[downstream].get(downstream_hour)
                if downstream_value is None:
                    continue
                residual = downstream_value - upstream_value
                residuals.append(residual)
                residual_rows.append(
                    {
                        "pair": pair_name,
                        "upstream_hour": _iso_z(upstream_hour),
                        "downstream_hour": _iso_z(downstream_hour),
                        "lag_hours": lag,
                        "upstream_discharge_cfs": round(upstream_value, 6),
                        "downstream_discharge_cfs": round(downstream_value, 6),
                        "downstream_minus_upstream_cfs": round(residual, 6),
                    }
                )
            if residuals:
                ordered = sorted(residuals)
                n = len(ordered)
                residual_summary_rows.append(
                    {
                        "pair": pair_name,
                        "lag_hours": lag,
                        "paired_hours": n,
                        "mean_residual_cfs": round(sum(residuals) / n, 6),
                        "median_residual_cfs": round(float(_median(residuals)), 6),
                        "p10_residual_cfs": round(ordered[int(0.10 * (n - 1))], 6),
                        "p90_residual_cfs": round(ordered[int(0.90 * (n - 1))], 6),
                        "fraction_positive": round(sum(1 for value in residuals if value > 0) / n, 6),
                        "status": "descriptive_residual_not_water_balance",
                    }
                )

    additive: dict[str, Any] = {}
    if all(name in overall_by_pair for name in ("Mathis_to_Bluntzer", "Bluntzer_to_Calallen", "Mathis_to_Calallen")):
        mb = overall_by_pair["Mathis_to_Bluntzer"]
        bc = overall_by_pair["Bluntzer_to_Calallen"]
        mc = overall_by_pair["Mathis_to_Calallen"]
        if all(row["best_lag_hours"] != "" for row in (mb, bc, mc)):
            expected = int(mb["best_lag_hours"]) + int(bc["best_lag_hours"])
            tight_sum_min = int(mb["lag_min_delta0005"]) + int(bc["lag_min_delta0005"])
            tight_sum_max = int(mb["lag_max_delta0005"]) + int(bc["lag_max_delta0005"])
            wide_sum_min = int(mb["lag_min_delta001"]) + int(bc["lag_min_delta001"])
            wide_sum_max = int(mb["lag_max_delta001"]) + int(bc["lag_max_delta001"])
            tight_overlap = _overlap(tight_sum_min, tight_sum_max, int(mc["lag_min_delta0005"]), int(mc["lag_max_delta0005"]))
            wide_overlap = _overlap(wide_sum_min, wide_sum_max, int(mc["lag_min_delta001"]), int(mc["lag_max_delta001"]))
            additive = {
                "short_reach_best_lag_sum_hours": expected,
                "direct_best_lag_hours": int(mc["best_lag_hours"]),
                "direct_minus_short_sum_hours": int(mc["best_lag_hours"]) - expected,
                "delta0005_short_sum_min": tight_sum_min,
                "delta0005_short_sum_max": tight_sum_max,
                "delta0005_direct_min": int(mc["lag_min_delta0005"]),
                "delta0005_direct_max": int(mc["lag_max_delta0005"]),
                "delta0005_overlap": bool(tight_overlap[0]),
                "delta0005_overlap_min": tight_overlap[1],
                "delta0005_overlap_max": tight_overlap[2],
                "delta001_short_sum_min": wide_sum_min,
                "delta001_short_sum_max": wide_sum_max,
                "delta001_direct_min": int(mc["lag_min_delta001"]),
                "delta001_direct_max": int(mc["lag_max_delta001"]),
                "delta001_overlap": bool(wide_overlap[0]),
                "delta001_overlap_min": wide_overlap[1],
                "delta001_overlap_max": wide_overlap[2],
                "interpretation": "descriptive_alignment_consistency_only",
            }

    output_dir.mkdir(parents=True, exist_ok=True)
    overall_path = output_dir / "overall_lag_peak_windows.csv"
    monthly_path = output_dir / "monthly_lag_stability.csv"
    rolling_path = output_dir / "rolling_lag_stability.csv"
    regime_path = output_dir / "flow_regime_lag_stability.csv"
    residual_path = output_dir / "lag_adjusted_residuals.csv"
    residual_summary_path = output_dir / "reach_residual_summary.csv"
    summary_path = output_dir / "lower_nueces_lag_stability_summary.json"
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
    _atomic_write_csv(overall_path, ["pair", "upstream_site_no", "downstream_site_no", *peak_fields, "status"], overall_rows)
    _atomic_write_csv(monthly_path, ["pair", "month", "window_start", "window_end_exclusive", *peak_fields, "status"], monthly_rows)
    _atomic_write_csv(rolling_path, ["pair", "window_days", "window_start", "window_end_exclusive", *peak_fields, "status"], rolling_rows)
    _atomic_write_csv(regime_path, ["pair", "regime", "upstream_tercile_low_cut_cfs", "upstream_tercile_high_cut_cfs", *peak_fields, "status"], regime_rows)
    _atomic_write_csv(
        residual_path,
        ["pair", "upstream_hour", "downstream_hour", "lag_hours", "upstream_discharge_cfs", "downstream_discharge_cfs", "downstream_minus_upstream_cfs"],
        residual_rows,
    )
    _atomic_write_csv(
        residual_summary_path,
        ["pair", "lag_hours", "paired_hours", "mean_residual_cfs", "median_residual_cfs", "p10_residual_cfs", "p90_residual_cfs", "fraction_positive", "status"],
        residual_summary_rows,
    )

    summary: dict[str, Any] = {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "build": BUILD_NUMBER,
        "analysis": "lower_nueces_lag_stability_and_reach_residuals",
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
        "rolling_days": list(rolling_days),
        "rolling_step_days": rolling_step_days,
        "overall_lag_peak_windows": overall_rows,
        "additive_consistency": additive,
        "monthly_row_count": len(monthly_rows),
        "rolling_row_count": len(rolling_rows),
        "flow_regime_row_count": len(regime_rows),
        "lag_adjusted_residual_row_count": len(residual_rows),
        "interpretation": {
            "causal_claim": False,
            "physical_travel_time_claim": False,
            "water_balance_claim": False,
            "peak_window_definition": "lags within 0.0005 or 0.001 Pearson-r units of the pair-specific maximum",
            "residual_definition": "downstream hourly mean at t+best_lag minus upstream hourly mean at t",
            "limitations": [
                "Lag stability is descriptive statistical alignment and is not proof of physical water-particle travel time.",
                "Lag-adjusted residuals are not a reach water balance and must not be assigned to groundwater, diversions, evaporation, tributaries, or any other cause without independent evidence.",
                "Reservoir operations, diversions, tributary inflows, reach storage, local gains or losses, backwater, regulation, and missing observations can affect all results.",
                "Flow regimes are upstream-discharge terciles within the requested analysis window, not regulatory or hydraulic classifications.",
            ],
        },
        "source_csv": str(csv_path.resolve()),
        "source_csv_bytes": int(index["source_csv_bytes"]),
        "source_csv_sha256": str(index["source_csv_sha256"]),
        "query_index": str(index_path.resolve()),
        "query_index_sha256": sha256_file(index_path),
    }

    for label, path in (
        ("overall_lag_peak_windows_csv", overall_path),
        ("monthly_lag_stability_csv", monthly_path),
        ("rolling_lag_stability_csv", rolling_path),
        ("flow_regime_lag_stability_csv", regime_path),
        ("lag_adjusted_residuals_csv", residual_path),
        ("reach_residual_summary_csv", residual_summary_path),
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
