"""Water Data for Texas coastal station harvest for NRHIS Build059."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


class CoastalHarvestError(RuntimeError):
    """Raised when coastal source data cannot be safely harvested."""


@dataclass(frozen=True)
class CoastalObservation:
    station_code: str
    station_name: str
    parameter_code: str
    parameter_name: str
    units: str
    observed_at: str
    value: float
    retrieved_at: str
    stale: bool
    source: str = "Water Data for Texas Coastal API"

    @property
    def identity(self) -> str:
        return f"{self.station_code}|{self.parameter_code}|{self.observed_at}"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else ["station_code"]
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


def _fetch_json(url: str, timeout_seconds: int) -> tuple[Any, bytes]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "NRHIS-Build059/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise CoastalHarvestError(f"Coastal API request failed: {url}: {exc}") from exc
    try:
        return json.loads(raw.decode("utf-8")), raw
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CoastalHarvestError(f"Coastal API returned invalid JSON: {url}") from exc


def normalize_parameters(payload: Any) -> dict[str, dict[str, str]]:
    if not isinstance(payload, list):
        raise CoastalHarvestError("Station parameter response was not a list")
    result: dict[str, dict[str, str]] = {}
    for row in payload:
        if not isinstance(row, dict):
            continue
        code = str(row.get("code") or "").strip()
        if not code:
            continue
        result[code] = {
            "name": str(row.get("name") or row.get("abbreviation") or code),
            "units": str(row.get("units_abbreviation") or row.get("units_name") or ""),
        }
    return result


def normalize_timeseries(
    payload: Any,
    *,
    station_code: str,
    station_name: str,
    parameter_code: str,
    parameter_name: str,
    units: str,
    retrieved_at: datetime,
    stale_hours: int,
) -> list[CoastalObservation]:
    if not isinstance(payload, list):
        raise CoastalHarvestError(f"Timeseries response for {parameter_code} was not a list")
    observations: list[CoastalObservation] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        timestamp = str(row.get("datetime_utc") or row.get("datetime") or "").strip()
        value = _number(row.get("value"))
        if not timestamp or value is None:
            continue
        observed = _parse_time(timestamp)
        observations.append(
            CoastalObservation(
                station_code=station_code,
                station_name=station_name,
                parameter_code=parameter_code,
                parameter_name=parameter_name,
                units=units,
                observed_at=_iso(observed),
                value=value,
                retrieved_at=_iso(retrieved_at),
                stale=(retrieved_at - observed) > timedelta(hours=stale_hours),
            )
        )
    unique = {item.identity: item for item in observations}
    return sorted(unique.values(), key=lambda item: item.observed_at)


def append_deduplicated_jsonl(path: Path, observations: list[CoastalObservation]) -> int:
    existing: set[str] = set()
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    existing.add(f"{row['station_code']}|{row['parameter_code']}|{row['observed_at']}")
    new_rows = [item for item in observations if item.identity not in existing]
    if new_rows:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="") as handle:
            for item in new_rows:
                handle.write(json.dumps(asdict(item), separators=(",", ":"), sort_keys=True) + "\n")
    return len(new_rows)


def harvest(config_path: Path, data_root: Path, *, retrieved_at: datetime | None = None) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    base = str(config.get("api_base", "https://waterdatafortexas.org/coastal/api")).rstrip("/")
    station_code = str(config["station_code"])
    station_name = str(config.get("station_name", station_code))
    timeout = int(config.get("timeout_seconds", 60))
    lookback_hours = int(config.get("lookback_hours", 72))
    stale_hours = int(config.get("stale_hours", 6))
    run_time = retrieved_at or utc_now()
    start_date = (run_time - timedelta(hours=lookback_hours)).date().isoformat()
    end_date = run_time.date().isoformat()
    stamp = run_time.strftime("%Y%m%dT%H%M%SZ")

    parameters_url = f"{base}/stations/{urllib.parse.quote(station_code)}/parameters"
    parameter_payload, parameter_raw = _fetch_json(parameters_url, timeout)
    available = normalize_parameters(parameter_payload)
    preferred = [str(item) for item in config.get("preferred_parameters", [])]
    selected = [code for code in preferred if code in available]
    if not selected:
        selected = sorted(available)
    required = {str(item) for item in config.get("required_parameters", [])}

    raw_dir = data_root / "raw" / "coastal" / "salt03" / stamp
    raw_records: list[dict[str, Any]] = []
    parameter_path = raw_dir / "parameters.json"
    _atomic_write(parameter_path, parameter_raw.decode("utf-8") + "\n")
    raw_records.append({"endpoint": "parameters", "path": str(parameter_path), "sha256": hashlib.sha256(parameter_raw).hexdigest()})

    all_observations: list[CoastalObservation] = []
    parameter_status: list[dict[str, Any]] = []
    for code in selected:
        query = urllib.parse.urlencode({"start_date": start_date, "end_date": end_date, "binning": str(config.get("binning", "hour"))})
        url = f"{base}/stations/{urllib.parse.quote(station_code)}/data/{urllib.parse.quote(code)}?{query}"
        try:
            payload, raw = _fetch_json(url, timeout)
            raw_path = raw_dir / f"{code}.json"
            _atomic_write(raw_path, raw.decode("utf-8") + "\n")
            raw_records.append({"endpoint": code, "path": str(raw_path), "sha256": hashlib.sha256(raw).hexdigest()})
            observations = normalize_timeseries(
                payload,
                station_code=station_code,
                station_name=station_name,
                parameter_code=code,
                parameter_name=available[code]["name"],
                units=available[code]["units"],
                retrieved_at=run_time,
                stale_hours=stale_hours,
            )
            all_observations.extend(observations)
            latest = observations[-1] if observations else None
            parameter_status.append({
                "parameter_code": code,
                "parameter_name": available[code]["name"],
                "units": available[code]["units"],
                "observation_count": len(observations),
                "latest_observed_at": latest.observed_at if latest else None,
                "latest_value": latest.value if latest else None,
                "stale": latest.stale if latest else True,
                "required": code in required,
                "error": "",
            })
        except CoastalHarvestError as exc:
            parameter_status.append({
                "parameter_code": code,
                "parameter_name": available[code]["name"],
                "units": available[code]["units"],
                "observation_count": 0,
                "latest_observed_at": None,
                "latest_value": None,
                "stale": True,
                "required": code in required,
                "error": str(exc),
            })

    current = [asdict(max((item for item in all_observations if item.parameter_code == code), key=lambda item: item.observed_at))
               for code in selected if any(item.parameter_code == code for item in all_observations)]
    history_path = data_root / "coastal" / "salt03_observations.jsonl"
    appended = append_deduplicated_jsonl(history_path, all_observations)
    current_json = data_root / "coastal" / "salt03_current_conditions.json"
    current_csv = data_root / "coastal" / "salt03_current_conditions.csv"
    status_csv = data_root / "coastal" / "salt03_parameter_status.csv"
    _atomic_write(current_json, json.dumps(current, indent=2, sort_keys=True) + "\n")
    _write_csv(current_csv, current)
    _write_csv(status_csv, parameter_status)

    missing_required = sorted(code for code in required if not any(row["parameter_code"] == code and row["observation_count"] for row in parameter_status))
    stale_required = sorted(row["parameter_code"] for row in parameter_status if row["required"] and row["stale"])
    readiness = {
        "schema_version": 1,
        "build": "059",
        "generated_at": _iso(run_time),
        "station_code": station_code,
        "ready_for_reporting": not missing_required and not stale_required,
        "missing_required_parameters": missing_required,
        "stale_required_parameters": stale_required,
        "parameters": parameter_status,
    }
    readiness_path = data_root / "coastal" / "salt03_readiness.json"
    _atomic_write(readiness_path, json.dumps(readiness, indent=2, sort_keys=True) + "\n")
    receipt = {
        "schema_version": 1,
        "build": "059",
        "completed_at": _iso(utc_now()),
        "station_code": station_code,
        "selected_parameters": selected,
        "observation_count": len(all_observations),
        "new_history_records": appended,
        "ready_for_reporting": readiness["ready_for_reporting"],
        "raw_records": raw_records,
        "files": {
            "current_json": str(current_json),
            "current_csv": str(current_csv),
            "parameter_status_csv": str(status_csv),
            "history_jsonl": str(history_path),
            "readiness": str(readiness_path),
        },
    }
    receipt_path = data_root / "receipts" / "salt03_coastal_harvest_receipt.json"
    _atomic_write(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    receipt["receipt_path"] = str(receipt_path)
    return receipt
