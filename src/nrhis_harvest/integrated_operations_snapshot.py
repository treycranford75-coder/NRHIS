"""Integrated NRHIS operations snapshot for Build060."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class IntegratedStationRow:
    station_id: str
    station_name: str
    station_type: str
    observed_at: str
    discharge_cfs: float | None
    gage_height_ft: float | None
    salinity_psu: float | None
    dissolved_oxygen_mg_l: float | None
    water_temperature_c: float | None
    specific_conductance_us_cm: float | None
    estimated_tds_mg_l: float | None
    forecast_category: str
    forecast_peak_value: float | None
    forecast_peak_at: str
    stale: bool
    status: str
    status_reasons: str


def _number(value: Any) -> float | None:
    try:
        return None if value in (None, "", "null") else float(value)
    except (TypeError, ValueError):
        return None


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _rows(value: Any, key: str | None = None) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    if isinstance(value, dict) and key and isinstance(value.get(key), list):
        return [row for row in value[key] if isinstance(row, dict)]
    return []


def _index(rows: list[dict[str, Any]], *keys: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        for key in keys:
            value = row.get(key)
            if value not in (None, ""):
                result[str(value)] = row
                break
    return result


def build_integrated_rows(
    basin_rows: list[dict[str, Any]],
    forecast_rows: list[dict[str, Any]],
    coastal_rows: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[IntegratedStationRow]:
    forecasts = _index(forecast_rows, "site_no", "station_id", "lid")
    result: list[IntegratedStationRow] = []

    for source in basin_rows:
        station_id = str(source.get("site_no") or source.get("station_id") or "")
        if not station_id:
            continue
        forecast = forecasts.get(station_id, {})
        reasons: list[str] = []
        discharge = _number(source.get("discharge_cfs"))
        gage_height = _number(source.get("gage_height_ft"))
        stale = bool(source.get("stale", False))
        if discharge is None and gage_height is None:
            reasons.append("current river observation missing")
        if stale:
            reasons.append("current river observation stale")
        status = "ready" if not reasons else "conditional"
        if discharge is None and gage_height is None:
            status = "not_ready"
        result.append(
            IntegratedStationRow(
                station_id=station_id,
                station_name=str(source.get("station_name") or station_id),
                station_type="river",
                observed_at=str(source.get("observed_at") or source.get("observation_time") or ""),
                discharge_cfs=discharge,
                gage_height_ft=gage_height,
                salinity_psu=None,
                dissolved_oxygen_mg_l=None,
                water_temperature_c=_number(source.get("water_temperature_c")),
                specific_conductance_us_cm=_number(source.get("specific_conductance_us_cm")),
                estimated_tds_mg_l=_number(source.get("estimated_tds_mg_l")),
                forecast_category=str(forecast.get("forecast_category") or "unavailable"),
                forecast_peak_value=_number(
                    forecast.get("forecast_peak_flow_cfs") or forecast.get("forecast_peak_stage_ft")
                ),
                forecast_peak_at=str(forecast.get("forecast_peak_at") or ""),
                stale=stale,
                status=status,
                status_reasons="; ".join(reasons),
            )
        )

    coastal_by_parameter = _index(coastal_rows, "parameter_code", "parameter_name")
    salinity = coastal_by_parameter.get("salinity") or coastal_by_parameter.get("Salinity") or {}
    if not salinity:
        for row in coastal_rows:
            if "salin" in str(row.get("parameter_name", "")).lower():
                salinity = row
                break
    station_code = str(config.get("coastal_station_code", "SALT03"))
    coastal_stale = bool(salinity.get("stale", True))
    coastal_reasons: list[str] = []
    salinity_value = _number(salinity.get("value"))
    if salinity_value is None:
        coastal_reasons.append("required SALT03 salinity observation missing")
    if coastal_stale:
        coastal_reasons.append("SALT03 salinity observation stale")
    coastal_status = "ready" if not coastal_reasons else "conditional"
    if salinity_value is None:
        coastal_status = "not_ready"

    def parameter_value(term: str) -> float | None:
        for row in coastal_rows:
            if term in str(row.get("parameter_name", "")).lower():
                return _number(row.get("value"))
        return None

    result.append(
        IntegratedStationRow(
            station_id=station_code,
            station_name=str(config.get("coastal_station_name", "SALT03 Nueces Bay")),
            station_type="coastal",
            observed_at=str(salinity.get("observed_at") or ""),
            discharge_cfs=None,
            gage_height_ft=None,
            salinity_psu=salinity_value,
            dissolved_oxygen_mg_l=parameter_value("dissolved oxygen"),
            water_temperature_c=parameter_value("temperature"),
            specific_conductance_us_cm=parameter_value("specific conductance"),
            estimated_tds_mg_l=None,
            forecast_category="not_applicable",
            forecast_peak_value=None,
            forecast_peak_at="",
            stale=coastal_stale,
            status=coastal_status,
            status_reasons="; ".join(coastal_reasons),
        )
    )
    return result


def run(config_path: Path, data_root: Path) -> dict[str, Any]:
    config = _load_json(config_path, {})
    basin_value = _load_json(data_root / "operational" / "basin_operational_snapshot.json", [])
    basin_rows = _rows(basin_value, "stations")
    forecast_value = _load_json(data_root / "nwps" / "nwps_forecasts.json", [])
    forecast_rows = _rows(forecast_value, "forecasts")
    coastal_value = _load_json(data_root / "coastal" / "salt03_current_conditions.json", [])
    coastal_rows = _rows(coastal_value, "observations")
    reservoir_value = _load_json(data_root / "reservoirs" / "reservoir_operations_summary.json", [])
    reservoir_rows = _rows(reservoir_value, "reservoirs")

    rows = [asdict(row) for row in build_integrated_rows(basin_rows, forecast_rows, coastal_rows, config)]
    not_ready = [row["station_id"] for row in rows if row["status"] == "not_ready"]
    conditional = [row["station_id"] for row in rows if row["status"] == "conditional"]
    reservoir_not_ready = [
        str(row.get("reservoir_id"))
        for row in reservoir_rows
        if row.get("operations_status") == "not_ready"
    ]
    overall = "ready"
    if conditional or any(row.get("operations_status") == "conditional" for row in reservoir_rows):
        overall = "conditional"
    if not_ready or reservoir_not_ready:
        overall = "not_ready"

    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    output = {
        "schema_version": 1,
        "build": "060",
        "generated_at": generated_at,
        "overall_status": overall,
        "stations": rows,
        "reservoirs": reservoir_rows,
        "release_gate": {
            "public_graphic_allowed": overall == "ready",
            "technical_report_allowed": overall in {"ready", "conditional"},
            "not_ready_stations": not_ready,
            "conditional_stations": conditional,
            "not_ready_reservoirs": reservoir_not_ready,
            "rule": "Hold public graphics until required live observations pass QA.",
        },
    }

    out_dir = data_root / "operational"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "integrated_operations_snapshot.json"
    csv_path = out_dir / "integrated_operations_snapshot.csv"
    readiness_path = out_dir / "integrated_reporting_readiness.json"
    json_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = list(rows[0].keys()) if rows else ["station_id"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    readiness_path.write_text(
        json.dumps(output["release_gate"] | {"overall_status": overall}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    receipt = {
        "schema_version": 1,
        "build": "060",
        "completed_at": generated_at,
        "overall_status": overall,
        "station_count": len(rows),
        "reservoir_count": len(reservoir_rows),
        "files": {
            "json": str(json_path),
            "csv": str(csv_path),
            "readiness": str(readiness_path),
        },
    }
    receipt_path = data_root / "receipts" / "integrated_operations_snapshot_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt["receipt_path"] = str(receipt_path)
    return receipt
