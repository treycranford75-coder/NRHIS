"""NOAA/NWS NWPS forecast and flood-threshold harvest for NRHIS Build054."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


class NwpsHarvestError(RuntimeError):
    """Raised when NWPS configuration or response data is invalid."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _fetch_json(url: str, timeout_seconds: int) -> tuple[dict[str, Any], bytes]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "NRHIS-Build054/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise NwpsHarvestError(f"NWPS request failed: {url}: {exc}") from exc
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NwpsHarvestError(f"NWPS returned invalid JSON: {url}") from exc
    if not isinstance(payload, dict):
        raise NwpsHarvestError(f"NWPS response was not an object: {url}")
    return payload, raw


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return None if number <= -9990 else number
    if isinstance(value, str):
        try:
            number = float(value.strip())
        except ValueError:
            return None
        return None if number <= -9990 else number
    if isinstance(value, dict):
        for key in ("value", "primary", "stage", "flow"):
            if key in value:
                result = _number(value[key])
                if result is not None:
                    return result
    return None


def _timestamp(row: dict[str, Any]) -> str | None:
    for key in ("validTime", "valid_time", "dateTime", "datetime", "timestamp", "time", "issuedTime"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _find_named_lists(node: Any, wanted: set[str], path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], list[Any]]]:
    matches: list[tuple[tuple[str, ...], list[Any]]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            next_path = path + (str(key),)
            if str(key).lower() in wanted and isinstance(value, list):
                matches.append((next_path, value))
            matches.extend(_find_named_lists(value, wanted, next_path))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            matches.extend(_find_named_lists(value, wanted, path + (str(index),)))
    return matches


def _normalize_series(payload: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    wanted = {kind, f"{kind}s", f"{kind}data", f"{kind}_data", f"{kind}values", f"{kind}_values"}
    candidates = _find_named_lists(payload, wanted)
    rows: list[dict[str, Any]] = []
    for path, values in candidates:
        for item in values:
            if not isinstance(item, dict):
                continue
            timestamp = _timestamp(item)
            if not timestamp:
                continue
            stage = _number(item.get("stage"))
            flow = _number(item.get("flow"))
            primary = _number(item.get("primary"))
            secondary = _number(item.get("secondary"))
            if stage is None and "stage" in "/".join(path).lower():
                stage = primary
            if flow is None and "flow" in "/".join(path).lower():
                flow = primary
            if stage is None and flow is None:
                stage = primary
                flow = secondary
            rows.append(
                {
                    "series": kind,
                    "valid_time": timestamp,
                    "stage": stage,
                    "flow": flow,
                    "source_path": "/".join(path),
                }
            )
    unique: dict[tuple[str, float | None, float | None], dict[str, Any]] = {}
    for row in rows:
        unique[(row["valid_time"], row["stage"], row["flow"])] = row
    return sorted(unique.values(), key=lambda row: row["valid_time"])


def normalize_categories(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    categories = metadata.get("categories") or {}
    if not isinstance(categories, dict):
        return []
    rows: list[dict[str, Any]] = []
    for category in ("action", "minor", "moderate", "major"):
        value = categories.get(category)
        if not isinstance(value, dict):
            value = {}
        rows.append(
            {
                "category": category,
                "stage": _number(value.get("stage")),
                "flow": _number(value.get("flow")),
            }
        )
    return rows


def classify_peak(peak_stage: float | None, peak_flow: float | None, thresholds: Iterable[dict[str, Any]]) -> str:
    rank = "not_defined"
    for threshold in thresholds:
        stage_hit = peak_stage is not None and threshold.get("stage") is not None and peak_stage >= threshold["stage"]
        flow_hit = peak_flow is not None and threshold.get("flow") is not None and peak_flow >= threshold["flow"]
        if stage_hit or flow_hit:
            rank = str(threshold["category"])
    return rank


def _peak(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"peak_stage": None, "peak_stage_time": None, "peak_flow": None, "peak_flow_time": None}
    stage_rows = [row for row in rows if row["stage"] is not None]
    flow_rows = [row for row in rows if row["flow"] is not None]
    stage_peak = max(stage_rows, key=lambda row: row["stage"]) if stage_rows else None
    flow_peak = max(flow_rows, key=lambda row: row["flow"]) if flow_rows else None
    return {
        "peak_stage": stage_peak["stage"] if stage_peak else None,
        "peak_stage_time": stage_peak["valid_time"] if stage_peak else None,
        "peak_flow": flow_peak["flow"] if flow_peak else None,
        "peak_flow_time": flow_peak["valid_time"] if flow_peak else None,
    }


def harvest(config_path: Path, output_root: Path, *, timeout_seconds: int | None = None, retrieved_at: datetime | None = None) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    gauges = config.get("gauges")
    if not isinstance(gauges, list) or not gauges:
        raise NwpsHarvestError("NWPS configuration contains no gauges")
    base = str(config.get("api_base", "https://api.water.noaa.gov/nwps/v1")).rstrip("/")
    timeout = int(timeout_seconds or config.get("timeout_seconds", 60))
    run_time = retrieved_at or _utc_now()
    stamp = run_time.strftime("%Y%m%dT%H%M%SZ")

    forecast_rows: list[dict[str, Any]] = []
    threshold_rows: list[dict[str, Any]] = []
    station_rows: list[dict[str, Any]] = []
    raw_records: list[dict[str, Any]] = []

    for gauge in gauges:
        identifier = str(gauge["identifier"])
        name = str(gauge["name"])
        station_status: dict[str, Any] = {
            "identifier": identifier,
            "usgs_site_no": str(gauge.get("usgs_site_no", identifier)),
            "station_name": name,
            "metadata_ok": False,
            "stageflow_ok": False,
            "forecast_points": 0,
            "forecast_available": False,
            "forecast_category": "not_defined",
            "error": "",
        }
        try:
            metadata, metadata_raw = _fetch_json(f"{base}/gauges/{identifier}", timeout)
            stageflow, stageflow_raw = _fetch_json(f"{base}/gauges/{identifier}/stageflow", timeout)
            station_status["metadata_ok"] = True
            station_status["stageflow_ok"] = True
            for endpoint, raw in (("metadata", metadata_raw), ("stageflow", stageflow_raw)):
                raw_path = output_root / "raw" / "nwps" / stamp / f"{identifier}_{endpoint}.json"
                _atomic_write(raw_path, raw.decode("utf-8") + ("\n" if not raw.endswith(b"\n") else ""))
                raw_records.append(
                    {
                        "identifier": identifier,
                        "endpoint": endpoint,
                        "path": str(raw_path),
                        "sha256": hashlib.sha256(raw).hexdigest(),
                        "bytes": len(raw),
                    }
                )
            thresholds = normalize_categories(metadata)
            for threshold in thresholds:
                threshold_rows.append({"identifier": identifier, "station_name": name, **threshold})
            forecasts = _normalize_series(stageflow, "forecast")
            observations = _normalize_series(stageflow, "observed")
            for row in forecasts:
                forecast_rows.append(
                    {
                        "identifier": identifier,
                        "usgs_site_no": station_status["usgs_site_no"],
                        "station_name": name,
                        **row,
                    }
                )
            peak = _peak(forecasts)
            station_status.update(peak)
            station_status["forecast_points"] = len(forecasts)
            station_status["forecast_available"] = bool(forecasts)
            station_status["observed_points_in_nwps"] = len(observations)
            station_status["forecast_category"] = classify_peak(peak["peak_stage"], peak["peak_flow"], thresholds)
        except Exception as exc:  # station-level isolation is intentional
            station_status["error"] = str(exc)
        station_rows.append(station_status)

    products = output_root / "nwps"
    _atomic_write(products / "nwps_forecasts.json", json.dumps(forecast_rows, indent=2, sort_keys=True) + "\n")
    _write_csv(
        products / "nwps_forecasts.csv",
        forecast_rows,
        ["identifier", "usgs_site_no", "station_name", "series", "valid_time", "stage", "flow", "source_path"],
    )
    _write_csv(
        products / "nwps_flood_thresholds.csv",
        threshold_rows,
        ["identifier", "station_name", "category", "stage", "flow"],
    )
    _write_csv(
        products / "nwps_station_status.csv",
        station_rows,
        [
            "identifier", "usgs_site_no", "station_name", "metadata_ok", "stageflow_ok",
            "forecast_points", "forecast_available", "observed_points_in_nwps", "peak_stage",
            "peak_stage_time", "peak_flow", "peak_flow_time", "forecast_category", "error",
        ],
    )
    readiness = {
        "schema_version": 1,
        "build": "053",
        "retrieved_at": _iso(run_time),
        "source_policy": config.get("source_policy", {}),
        "configured_gauges": len(gauges),
        "successful_gauges": sum(1 for row in station_rows if row["metadata_ok"] and row["stageflow_ok"]),
        "gauges_with_forecasts": sum(1 for row in station_rows if row["forecast_available"]),
        "forecast_points": len(forecast_rows),
        "threshold_records": len(threshold_rows),
        "ready_for_reporting": all(row["metadata_ok"] and row["stageflow_ok"] for row in station_rows),
        "stations": station_rows,
    }
    _atomic_write(products / "nwps_readiness.json", json.dumps(readiness, indent=2, sort_keys=True) + "\n")
    receipt = {
        "schema_version": 1,
        "build": "053",
        "retrieved_at": _iso(run_time),
        "api_base": base,
        "raw_responses": raw_records,
        "products": {
            "forecast_json": str(products / "nwps_forecasts.json"),
            "forecast_csv": str(products / "nwps_forecasts.csv"),
            "threshold_csv": str(products / "nwps_flood_thresholds.csv"),
            "station_status_csv": str(products / "nwps_station_status.csv"),
            "readiness_json": str(products / "nwps_readiness.json"),
        },
        "summary": {key: readiness[key] for key in ("configured_gauges", "successful_gauges", "gauges_with_forecasts", "forecast_points", "threshold_records", "ready_for_reporting")},
    }
    receipt_path = output_root / "receipts" / "nwps_forecast_harvest_receipt.json"
    _atomic_write(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    receipt["receipt_path"] = str(receipt_path)
    return receipt
