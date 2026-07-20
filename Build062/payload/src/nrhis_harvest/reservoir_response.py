"""Estimated reservoir response calculations for NRHIS Build057."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SECONDS_PER_DAY = 86400.0
CUBIC_FEET_PER_ACRE_FOOT = 43560.0


@dataclass(frozen=True)
class ReservoirResponse:
    reservoir_id: str
    reservoir_name: str
    current_storage_acft: float | None
    conservation_capacity_acft: float | None
    current_percent_full: float | None
    estimated_event_gain_low_acft: float | None
    estimated_event_gain_central_acft: float | None
    estimated_event_gain_high_acft: float | None
    projected_storage_low_acft: float | None
    projected_storage_central_acft: float | None
    projected_storage_high_acft: float | None
    projected_percent_full_low: float | None
    projected_percent_full_central: float | None
    projected_percent_full_high: float | None
    confidence: str
    basis: str
    caveat: str


def _num(value: Any) -> float | None:
    try:
        return None if value in (None, "", "null") else float(value)
    except (TypeError, ValueError):
        return None


def cfs_hours_to_acft(flow_cfs: float | None, hours: float | None) -> float | None:
    if flow_cfs is None or hours is None or flow_cfs < 0 or hours < 0:
        return None
    return round(flow_cfs * hours * 3600.0 / CUBIC_FEET_PER_ACRE_FOOT, 2)


def _forecast_volume(rows: list[dict[str, Any]], station_ids: set[str], window_hours: float) -> float | None:
    volumes: list[float] = []
    for row in rows:
        if str(row.get("station_id")) not in station_ids:
            continue
        peak = _num(row.get("forecast_peak_flow_cfs") or row.get("peak_flow_cfs"))
        if peak is not None:
            volume = cfs_hours_to_acft(peak, window_hours)
            if volume is not None:
                volumes.append(volume)
    return max(volumes) if volumes else None


def estimate_responses(
    reservoirs: list[dict[str, Any]],
    forecasts: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[ReservoirResponse]:
    station_map = {
        "ChokeCanyon": {"08194500", "08200000", "08201000"},
        "CorpusChristi": {"08210000", "08211000", "08211200"},
    }
    results: list[ReservoirResponse] = []
    for reservoir in reservoirs:
        rid = str(reservoir.get("reservoir_id", ""))
        if rid not in config.get("reservoirs", {}):
            continue
        storage = _num(reservoir.get("conservation_storage_acft"))
        capacity = _num(reservoir.get("conservation_capacity_acft"))
        percent = _num(reservoir.get("percent_full"))
        window = _num(config.get("routing_windows_hours", {}).get(rid))
        gross = _forecast_volume(forecasts, station_map.get(rid, set()), window or 0)
        factors = config.get("routing_capture_factors", {}).get(rid, {})
        gains = {
            key: round(gross * float(factors[key]), 2) if gross is not None and key in factors else None
            for key in ("low", "central", "high")
        }
        projected = {
            key: min(capacity, storage + gains[key])
            if capacity is not None and storage is not None and gains[key] is not None
            else None
            for key in gains
        }
        projected_pct = {
            key: round(projected[key] / capacity * 100.0, 1)
            if projected[key] is not None and capacity
            else None
            for key in projected
        }
        confidence = "moderate" if gross is not None and storage is not None and capacity else "low"
        basis = (
            "Latest available NWPS peak-flow forecast converted to a routing-window volume and "
            "scaled by configured low/central/high capture factors."
            if gross is not None
            else "No usable NWPS peak-flow forecast was available for the configured upstream stations."
        )
        caveat = (
            "Estimate based on the latest available hydrographs, routing assumptions, reservoir conditions, "
            "and forecasts; values will change as new data arrive."
        )
        results.append(
            ReservoirResponse(
                reservoir_id=rid,
                reservoir_name=str(reservoir.get("reservoir_name") or config["reservoirs"][rid]["display_name"]),
                current_storage_acft=storage,
                conservation_capacity_acft=capacity,
                current_percent_full=percent,
                estimated_event_gain_low_acft=gains["low"],
                estimated_event_gain_central_acft=gains["central"],
                estimated_event_gain_high_acft=gains["high"],
                projected_storage_low_acft=projected["low"],
                projected_storage_central_acft=projected["central"],
                projected_storage_high_acft=projected["high"],
                projected_percent_full_low=projected_pct["low"],
                projected_percent_full_central=projected_pct["central"],
                projected_percent_full_high=projected_pct["high"],
                confidence=confidence,
                basis=basis,
                caveat=caveat,
            )
        )
    return results


def run(config_path: Path, data_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    reservoirs_path = data_root / "reservoirs" / "reservoir_current_conditions.json"
    forecasts_path = data_root / "nwps" / "nwps_forecasts.json"
    reservoirs = json.loads(reservoirs_path.read_text(encoding="utf-8"))
    forecasts = json.loads(forecasts_path.read_text(encoding="utf-8")) if forecasts_path.exists() else []
    rows = [asdict(x) for x in estimate_responses(reservoirs, forecasts, config)]
    out_dir = data_root / "reservoirs"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "reservoir_response_estimate.json"
    csv_path = out_dir / "reservoir_response_estimate.csv"
    json_path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["reservoir_id"])
        writer.writeheader(); writer.writerows(rows)
    receipt = {
        "schema_version": 1,
        "build": "057",
        "completed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "reservoir_count": len(rows),
        "files": {"json": str(json_path), "csv": str(csv_path)},
    }
    receipt_path = data_root / "receipts" / "reservoir_response_estimate_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt["receipt_path"] = str(receipt_path)
    return receipt
