"""Build101 lower Nueces station-to-station discharge analysis.

This module operates only on the finalized local NRHIS historical archive. It
aggregates instantaneous discharge to hourly means, evaluates descriptive lagged
correlations among Mathis, Bluntzer, and Calallen, and writes hash-bound evidence
outputs. Lag correlations are statistical alignments, not causal attribution or
proof of physical travel time.
"""
from __future__ import annotations

import csv
import json
import math
import os
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from nrhis_analysis.usgs_history_query import (
    QueryError,
    load_sparse_index,
    normalize_window,
    query_history,
    sha256_file,
)

BUILD_NUMBER = "101"
ANALYSIS_SCHEMA_VERSION = 1
DISCHARGE_PARAMETER = "00060"
DEFAULT_SITE_NOS = ("08211000", "08211200", "08211500")
SITE_NAMES = {
    "08211000": "Nueces River near Mathis, TX",
    "08211200": "Nueces River at Bluntzer, TX",
    "08211500": "Nueces River at Calallen, TX",
}
PAIR_SPECS = (
    ("Mathis_to_Bluntzer", "08211000", "08211200"),
    ("Bluntzer_to_Calallen", "08211200", "08211500"),
    ("Mathis_to_Calallen", "08211000", "08211500"),
)


@dataclass
class HourAccumulator:
    count: int = 0
    total: float = 0.0
    minimum: float | None = None
    maximum: float | None = None

    def add(self, value: float) -> None:
        self.count += 1
        self.total += value
        self.minimum = value if self.minimum is None else min(self.minimum, value)
        self.maximum = value if self.maximum is None else max(self.maximum, value)

    @property
    def mean(self) -> float:
        return self.total / self.count


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


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _hour_start(value: datetime) -> datetime:
    return value.replace(minute=0, second=0, microsecond=0)


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


def _build_hourly(
    rows: Iterable[dict[str, str]],
    *,
    site_nos: tuple[str, ...],
    min_observations_per_hour: int,
) -> tuple[list[dict[str, Any]], dict[str, dict[datetime, float]], dict[str, Any]]:
    accumulators: dict[tuple[str, datetime], HourAccumulator] = defaultdict(HourAccumulator)
    raw_counts: dict[str, int] = {site: 0 for site in site_nos}
    valid_counts: dict[str, int] = {site: 0 for site in site_nos}

    for row in rows:
        site = str(row.get("site_no", ""))
        if site not in raw_counts:
            continue
        raw_counts[site] += 1
        value = _parse_float(row.get("value", ""))
        if value is None:
            continue
        valid_counts[site] += 1
        hour = _hour_start(_parse_time(row["observed_at"]))
        accumulators[(site, hour)].add(value)

    hourly_rows: list[dict[str, Any]] = []
    hourly_values: dict[str, dict[datetime, float]] = {site: {} for site in site_nos}
    excluded_bins: dict[str, int] = {site: 0 for site in site_nos}

    for (site, hour), acc in sorted(accumulators.items(), key=lambda item: (item[0][1], item[0][0])):
        if acc.count < min_observations_per_hour:
            excluded_bins[site] += 1
            continue
        mean_value = acc.mean
        hourly_values[site][hour] = mean_value
        hourly_rows.append(
            {
                "observed_hour": _iso_z(hour),
                "site_no": site,
                "site_name": SITE_NAMES.get(site, site),
                "observation_count": acc.count,
                "mean_discharge_cfs": round(mean_value, 6),
                "minimum_discharge_cfs": round(float(acc.minimum), 6),
                "maximum_discharge_cfs": round(float(acc.maximum), 6),
            }
        )

    coverage = {
        site: {
            "raw_discharge_records": raw_counts[site],
            "valid_discharge_records": valid_counts[site],
            "hourly_bins_retained": len(hourly_values[site]),
            "hourly_bins_excluded_low_count": excluded_bins[site],
        }
        for site in site_nos
    }
    return hourly_rows, hourly_values, coverage


def _daily_summary(hourly_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in hourly_rows:
        date_key = str(row["observed_hour"])[:10]
        grouped[(str(row["site_no"]), date_key)].append(float(row["mean_discharge_cfs"]))

    result: list[dict[str, Any]] = []
    for (site, date_key), values in sorted(grouped.items(), key=lambda item: (item[0][1], item[0][0])):
        result.append(
            {
                "date": date_key,
                "site_no": site,
                "site_name": SITE_NAMES.get(site, site),
                "hourly_bins": len(values),
                "mean_hourly_discharge_cfs": round(sum(values) / len(values), 6),
                "minimum_hourly_discharge_cfs": round(min(values), 6),
                "maximum_hourly_discharge_cfs": round(max(values), 6),
            }
        )
    return result


def _lag_rows(
    hourly_values: dict[str, dict[datetime, float]],
    *,
    max_lag_hours: int,
    min_paired_hours: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    all_rows: list[dict[str, Any]] = []
    best_rows: list[dict[str, Any]] = []

    for pair_name, upstream, downstream in PAIR_SPECS:
        upstream_values = hourly_values.get(upstream, {})
        downstream_values = hourly_values.get(downstream, {})
        pair_results: list[dict[str, Any]] = []

        for lag in range(max_lag_hours + 1):
            xs: list[float] = []
            ys: list[float] = []
            for upstream_hour, upstream_value in upstream_values.items():
                downstream_hour = upstream_hour + timedelta(hours=lag)
                if downstream_hour in downstream_values:
                    xs.append(upstream_value)
                    ys.append(downstream_values[downstream_hour])
            r = _pearson(xs, ys) if len(xs) >= min_paired_hours else None
            row = {
                "pair": pair_name,
                "upstream_site_no": upstream,
                "downstream_site_no": downstream,
                "lag_hours": lag,
                "paired_hours": len(xs),
                "pearson_r": "" if r is None else round(r, 8),
                "status": "insufficient_pairs" if r is None else "descriptive_only",
            }
            pair_results.append(row)
            all_rows.append(row)

        eligible = [row for row in pair_results if row["pearson_r"] != ""]
        if eligible:
            best = max(eligible, key=lambda row: float(row["pearson_r"]))
            best_rows.append(dict(best))
        else:
            best_rows.append(
                {
                    "pair": pair_name,
                    "upstream_site_no": upstream,
                    "downstream_site_no": downstream,
                    "lag_hours": "",
                    "paired_hours": 0,
                    "pearson_r": "",
                    "status": "insufficient_pairs",
                }
            )

    return all_rows, best_rows


def analyze_lower_nueces_flow_network(
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
) -> dict[str, Any]:
    """Analyze descriptive discharge relationships along the lower Nueces main stem."""
    if min_observations_per_hour < 1:
        raise QueryError("min_observations_per_hour must be at least 1")
    if max_lag_hours < 0:
        raise QueryError("max_lag_hours must be nonnegative")
    if min_paired_hours < 2:
        raise QueryError("min_paired_hours must be at least 2")

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
    hourly_rows, hourly_values, coverage = _build_hourly(
        rows,
        site_nos=site_nos,
        min_observations_per_hour=min_observations_per_hour,
    )
    daily_rows = _daily_summary(hourly_rows)
    lag_rows, best_rows = _lag_rows(
        hourly_values,
        max_lag_hours=max_lag_hours,
        min_paired_hours=min_paired_hours,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    hourly_path = output_dir / "hourly_discharge.csv"
    daily_path = output_dir / "daily_station_summary.csv"
    lag_path = output_dir / "pair_lag_correlations.csv"
    best_path = output_dir / "pair_best_lags.csv"
    summary_path = output_dir / "lower_nueces_flow_network_summary.json"
    receipt_path = output_dir / "analysis-receipt.json"

    _atomic_write_csv(
        hourly_path,
        [
            "observed_hour",
            "site_no",
            "site_name",
            "observation_count",
            "mean_discharge_cfs",
            "minimum_discharge_cfs",
            "maximum_discharge_cfs",
        ],
        hourly_rows,
    )
    _atomic_write_csv(
        daily_path,
        [
            "date",
            "site_no",
            "site_name",
            "hourly_bins",
            "mean_hourly_discharge_cfs",
            "minimum_hourly_discharge_cfs",
            "maximum_hourly_discharge_cfs",
        ],
        daily_rows,
    )
    _atomic_write_csv(
        lag_path,
        ["pair", "upstream_site_no", "downstream_site_no", "lag_hours", "paired_hours", "pearson_r", "status"],
        lag_rows,
    )
    _atomic_write_csv(
        best_path,
        ["pair", "upstream_site_no", "downstream_site_no", "lag_hours", "paired_hours", "pearson_r", "status"],
        best_rows,
    )

    summary: dict[str, Any] = {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "build": BUILD_NUMBER,
        "analysis": "lower_nueces_station_to_station_discharge",
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
        "min_observations_per_hour": min_observations_per_hour,
        "max_lag_hours": max_lag_hours,
        "min_paired_hours": min_paired_hours,
        "hourly_row_count": len(hourly_rows),
        "daily_row_count": len(daily_rows),
        "best_lag_results": best_rows,
        "interpretation": {
            "lag_meaning": "positive lag compares upstream hour t with downstream hour t+lag",
            "causal_claim": False,
            "physical_travel_time_claim": False,
            "limitations": [
                "Lag correlation is descriptive statistical alignment, not proof of water-particle travel time.",
                "Reservoir releases, diversions, tributary inflows, local gains or losses, backwater, regulation, and missing observations can affect station relationships.",
                "Hourly values are means of retained instantaneous observations and are not daily mean discharge products.",
            ],
        },
        "source_csv": str(csv_path.resolve()),
        "source_csv_bytes": int(index["source_csv_bytes"]),
        "source_csv_sha256": str(index["source_csv_sha256"]),
        "query_index": str(index_path.resolve()),
        "query_index_sha256": sha256_file(index_path),
        "hourly_discharge_csv": str(hourly_path.resolve()),
        "hourly_discharge_csv_sha256": sha256_file(hourly_path),
        "daily_station_summary_csv": str(daily_path.resolve()),
        "daily_station_summary_csv_sha256": sha256_file(daily_path),
        "pair_lag_correlations_csv": str(lag_path.resolve()),
        "pair_lag_correlations_csv_sha256": sha256_file(lag_path),
        "pair_best_lags_csv": str(best_path.resolve()),
        "pair_best_lags_csv_sha256": sha256_file(best_path),
    }
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
        "hourly_discharge_csv_sha256": summary["hourly_discharge_csv_sha256"],
        "daily_station_summary_csv_sha256": summary["daily_station_summary_csv_sha256"],
        "pair_lag_correlations_csv_sha256": summary["pair_lag_correlations_csv_sha256"],
        "pair_best_lags_csv_sha256": summary["pair_best_lags_csv_sha256"],
        "causation_claimed": False,
        "physical_travel_time_claimed": False,
    }
    _atomic_write_json(receipt_path, receipt)
    summary["receipt"] = str(receipt_path.resolve())
    summary["receipt_sha256"] = sha256_file(receipt_path)
    return summary
