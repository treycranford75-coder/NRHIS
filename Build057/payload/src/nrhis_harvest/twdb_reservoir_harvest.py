"""TWDB/Water Data for Texas reservoir harvest for NRHIS Build055."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
import urllib.request
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable


class ReservoirHarvestError(RuntimeError):
    """Raised when reservoir source data cannot be safely normalized."""


@dataclass(frozen=True)
class ReservoirObservation:
    reservoir_id: str
    reservoir_name: str
    observed_date: str
    elevation_ft: float | None
    conservation_storage_acft: float | None
    conservation_capacity_acft: float | None
    percent_full: float | None
    surface_area_acres: float | None
    volume_acft: float | None
    storage_change_acft: float | None
    stale: bool
    source: str = "TWDB Water Data for Texas"

    @property
    def identity(self) -> str:
        return f"{self.reservoir_id}|{self.observed_date}"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


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
    fields = list(rows[0].keys()) if rows else ["reservoir_id"]
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


def _number(value: Any) -> float | None:
    if value in (None, "", "null"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_bytes(url: str, timeout_seconds: int = 60) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "NRHIS/0.1 Build055 (+https://github.com/treycranford75-coder/NRHIS)"},
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        if getattr(response, "status", 200) != 200:
            raise ReservoirHarvestError(f"Reservoir source returned HTTP {response.status}")
        return response.read()


def _prior_storage(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    result: dict[str, float] = {}
    if isinstance(rows, list):
        for row in rows:
            value = _number(row.get("conservation_storage_acft")) if isinstance(row, dict) else None
            key = str(row.get("reservoir_id", "")) if isinstance(row, dict) else ""
            if key and value is not None:
                result[key] = value
    return result


def parse_geojson(
    payload: dict[str, Any],
    config: dict[str, Any],
    *,
    now: datetime,
    prior_storage: dict[str, float] | None = None,
) -> list[ReservoirObservation]:
    features = payload.get("features")
    if not isinstance(features, list):
        raise ReservoirHarvestError("Reservoir payload is missing a GeoJSON features list")
    configured = {str(item["condensed_name"]): item for item in config.get("reservoirs", [])}
    if not configured:
        raise ReservoirHarvestError("Reservoir configuration contains no reservoirs")
    prior = prior_storage or {}
    stale_days = int(config.get("stale_days", 3))
    observations: list[ReservoirObservation] = []
    for feature in features:
        props = feature.get("properties") if isinstance(feature, dict) else None
        if not isinstance(props, dict):
            continue
        reservoir_id = str(props.get("condensed_name", ""))
        if reservoir_id not in configured:
            continue
        observed_date = str(props.get("timestamp", ""))
        try:
            observed = date.fromisoformat(observed_date)
        except ValueError as exc:
            raise ReservoirHarvestError(f"Invalid reservoir timestamp for {reservoir_id}: {observed_date}") from exc
        age_days = (now.date() - observed).days
        storage = _number(props.get("conservation_storage"))
        previous = prior.get(reservoir_id)
        change = round(storage - previous, 2) if storage is not None and previous is not None else None
        observations.append(
            ReservoirObservation(
                reservoir_id=reservoir_id,
                reservoir_name=str(props.get("full_name") or configured[reservoir_id].get("display_name") or reservoir_id),
                observed_date=observed_date,
                elevation_ft=_number(props.get("elevation")),
                conservation_storage_acft=storage,
                conservation_capacity_acft=_number(props.get("conservation_capacity")),
                percent_full=_number(props.get("percent_full")),
                surface_area_acres=_number(props.get("area")),
                volume_acft=_number(props.get("volume")),
                storage_change_acft=change,
                stale=age_days > stale_days,
            )
        )
    missing = sorted(set(configured) - {item.reservoir_id for item in observations})
    if missing:
        raise ReservoirHarvestError(f"Configured reservoirs missing from source payload: {', '.join(missing)}")
    order = {key: int(value.get("display_order", 999)) for key, value in configured.items()}
    return sorted(observations, key=lambda item: order.get(item.reservoir_id, 999))


def append_deduplicated_jsonl(path: Path, observations: Iterable[ReservoirObservation]) -> int:
    existing: set[str] = set()
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    existing.add(f"{row['reservoir_id']}|{row['observed_date']}")
    new_rows = [item for item in observations if item.identity not in existing]
    if new_rows:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="") as handle:
            for item in new_rows:
                handle.write(json.dumps(asdict(item), separators=(",", ":"), sort_keys=True) + "\n")
    return len(new_rows)


def harvest(config_path: Path, data_root: Path, *, timeout_seconds: int | None = None) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    url = str(config["api_url"])
    timeout = int(timeout_seconds or config.get("timeout_seconds", 60))
    started = utc_now()
    current_json = data_root / "reservoirs" / "reservoir_current_conditions.json"
    prior = _prior_storage(current_json)
    raw = fetch_bytes(url, timeout_seconds=timeout)
    payload = json.loads(raw.decode("utf-8"))
    observations = parse_geojson(payload, config, now=started, prior_storage=prior)

    stamp = started.strftime("%Y%m%dT%H%M%SZ")
    raw_path = data_root / "raw" / "twdb_reservoirs" / f"reservoirs-{stamp}.geojson"
    _atomic_write(raw_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")

    history_path = data_root / "reservoirs" / "reservoir_observations.jsonl"
    appended = append_deduplicated_jsonl(history_path, observations)
    rows = [asdict(item) for item in observations]
    _atomic_write(current_json, json.dumps(rows, indent=2, sort_keys=True) + "\n")
    current_csv = data_root / "reservoirs" / "reservoir_current_conditions.csv"
    _write_csv(current_csv, rows)

    total_storage = sum(item.conservation_storage_acft or 0.0 for item in observations)
    total_capacity = sum(item.conservation_capacity_acft or 0.0 for item in observations)
    combined = {
        "schema_version": 1,
        "build": "055",
        "generated_at": started.isoformat().replace("+00:00", "Z"),
        "source": "TWDB Water Data for Texas",
        "reservoir_count": len(observations),
        "combined_conservation_storage_acft": round(total_storage, 2),
        "combined_conservation_capacity_acft": round(total_capacity, 2),
        "combined_percent_full": round(total_storage / total_capacity * 100, 1) if total_capacity else None,
        "stale_reservoirs": [item.reservoir_id for item in observations if item.stale],
        "reservoirs": rows,
    }
    combined_path = data_root / "reservoirs" / "reservoir_combined_summary.json"
    _atomic_write(combined_path, json.dumps(combined, indent=2, sort_keys=True) + "\n")

    receipt = {
        "schema_version": 1,
        "build": "055",
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "completed_at": utc_now().isoformat().replace("+00:00", "Z"),
        "request_url": url,
        "reservoir_count": len(observations),
        "new_history_records": appended,
        "stale_reservoirs": combined["stale_reservoirs"],
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "files": {
            "raw": str(raw_path),
            "current_json": str(current_json),
            "current_csv": str(current_csv),
            "history_jsonl": str(history_path),
            "combined_summary": str(combined_path),
        },
    }
    receipt_path = data_root / "receipts" / "twdb_reservoir_harvest_receipt.json"
    _atomic_write(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    receipt["receipt_path"] = str(receipt_path)
    return receipt
