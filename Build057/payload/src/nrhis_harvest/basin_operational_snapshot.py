"""Integrate USGS observations, USGS quality, and NWPS forecasts for NRHIS."""
from __future__ import annotations

import csv
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SnapshotError(RuntimeError):
    """Raised when required operational inputs are missing or malformed."""


def _read_json(path: Path) -> Any:
    if not path.exists():
        raise SnapshotError(f"Required input is missing: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _parameter_map(observations: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    result: dict[str, dict[str, dict[str, Any]]] = {}
    for row in observations:
        site = str(row.get("site_no", ""))
        code = str(row.get("parameter_code", ""))
        if site and code:
            result.setdefault(site, {})[code] = row
    return result


def _severity(category: str) -> int:
    return {"major": 5, "moderate": 4, "minor": 3, "action": 2, "not_defined": 0}.get(category, 1)


def build_snapshot(config_path: Path, data_root: Path, *, generated_at: datetime | None = None) -> dict[str, Any]:
    config = _read_json(config_path)
    stations = config.get("stations")
    if not isinstance(stations, list) or not stations:
        raise SnapshotError("Snapshot configuration contains no stations")

    observations = _read_json(data_root / "current" / "usgs_current_conditions.json")
    nwps = _read_json(data_root / "nwps" / "nwps_readiness.json")
    quality_path = data_root / "quality" / "usgs_data_quality_summary.json"
    quality = _read_json(quality_path) if quality_path.exists() else {"ready_for_reporting": False, "stations": []}
    if not isinstance(observations, list):
        raise SnapshotError("USGS current conditions must be a list")

    by_site = _parameter_map(observations)
    nwps_by_site = {str(row.get("usgs_site_no", "")): row for row in nwps.get("stations", [])}
    quality_by_site = {str(row.get("site_no", "")): row for row in quality.get("stations", []) if isinstance(row, dict)}
    rows: list[dict[str, Any]] = []

    for station in stations:
        site = str(station["site_no"])
        obs = by_site.get(site, {})
        forecast = nwps_by_site.get(site, {})
        qrow = quality_by_site.get(site, {})
        discharge = obs.get("00060", {})
        stage = obs.get("00065", {})
        conductance = obs.get("00095", {})
        category = str(forecast.get("forecast_category", "not_defined"))
        stale = any(bool(item.get("stale")) for item in obs.values())
        missing_required = [code for code in station.get("required_parameters", []) if code not in obs]
        forecast_available = bool(forecast.get("forecast_available", False))
        alert_score = _severity(category) * 10 + (3 if stale else 0) + len(missing_required) * 5
        rows.append({
            "site_no": site,
            "station_name": station["name"],
            "river_segment": station.get("segment", ""),
            "display_order": int(station.get("display_order", 999)),
            "observed_discharge_cfs": discharge.get("value"),
            "observed_stage_ft": stage.get("value"),
            "specific_conductance_us_cm": conductance.get("value"),
            "estimated_tds_mg_l": conductance.get("estimated_tds_mg_l"),
            "latest_observed_at": max((str(v.get("observed_at", "")) for v in obs.values()), default=""),
            "observation_stale": stale,
            "missing_required_parameters": ";".join(missing_required),
            "forecast_available": forecast_available,
            "forecast_category": category,
            "forecast_peak_stage_ft": forecast.get("peak_stage"),
            "forecast_peak_stage_time": forecast.get("peak_stage_time"),
            "forecast_peak_flow_cfs": forecast.get("peak_flow"),
            "forecast_peak_flow_time": forecast.get("peak_flow_time"),
            "quality_status": qrow.get("status", "unknown"),
            "alert_score": alert_score,
        })

    rows.sort(key=lambda row: row["display_order"])
    blocking = [r for r in rows if r["observation_stale"] or r["missing_required_parameters"]]
    forecast_alerts = [r for r in rows if _severity(r["forecast_category"]) >= 2]
    ready = not blocking and bool(nwps.get("ready_for_reporting", False)) and bool(quality.get("ready_for_reporting", False))
    generated = generated_at or datetime.now(timezone.utc)
    result = {
        "schema_version": 1,
        "build": "055",
        "generated_at": generated.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_policy": {
            "observations": "USGS Instantaneous Values API",
            "forecasts_and_thresholds": "NOAA/NWS NWPS",
            "estimated_tds": "specific conductance x 0.65; estimate only",
        },
        "ready_for_reporting": ready,
        "station_count": len(rows),
        "blocking_station_count": len(blocking),
        "forecast_alert_count": len(forecast_alerts),
        "highest_forecast_category": max((r["forecast_category"] for r in rows), key=_severity, default="not_defined"),
        "stations": rows,
    }
    products = data_root / "operational"
    json_path = products / "basin_operational_snapshot.json"
    csv_path = products / "basin_operational_snapshot.csv"
    alerts_path = products / "basin_operational_alerts.csv"
    readiness_path = products / "basin_reporting_readiness.json"
    _atomic_write(json_path, json.dumps(result, indent=2, sort_keys=True) + "\n")
    fields = list(rows[0].keys()) if rows else ["site_no"]
    _write_csv(csv_path, rows, fields)
    _write_csv(alerts_path, sorted([r for r in rows if r["alert_score"] > 0], key=lambda r: (-r["alert_score"], r["display_order"])), fields)
    _atomic_write(readiness_path, json.dumps({k: result[k] for k in ("schema_version", "build", "generated_at", "ready_for_reporting", "blocking_station_count", "forecast_alert_count", "highest_forecast_category")}, indent=2, sort_keys=True) + "\n")
    receipt = {
        "schema_version": 1,
        "build": "055",
        "generated_at": result["generated_at"],
        "ready_for_reporting": ready,
        "products": {"snapshot_json": str(json_path), "snapshot_csv": str(csv_path), "alerts_csv": str(alerts_path), "readiness_json": str(readiness_path)},
    }
    receipt_path = data_root / "receipts" / "basin_operational_snapshot_receipt.json"
    _atomic_write(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    receipt["receipt_path"] = str(receipt_path)
    return receipt
