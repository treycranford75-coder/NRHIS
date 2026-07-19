"""Production USGS instantaneous-value harvest for the Nueces River basin.

Build050 deliberately uses only the Python standard library so the operational
harvester can run on a clean NRHIS workstation without adding a new dependency.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

USGS_IV_ENDPOINT = "https://waterservices.usgs.gov/nwis/iv/"
PARAMETERS = {
    "00060": ("discharge", "ft3/s"),
    "00065": ("gage_height", "ft"),
    "00010": ("water_temperature", "degC"),
    "00095": ("specific_conductance", "uS/cm"),
}


@dataclass(frozen=True)
class Observation:
    site_no: str
    site_name: str
    parameter_code: str
    parameter_name: str
    unit: str
    observed_at: str
    value: float | None
    qualifiers: tuple[str, ...]
    provisional: bool
    stale: bool
    estimated_tds_mg_l: float | None
    source: str = "USGS Instantaneous Values API"

    @property
    def identity(self) -> str:
        return f"{self.site_no}|{self.parameter_code}|{self.observed_at}"


class HarvestError(RuntimeError):
    """Raised when the upstream payload cannot be safely harvested."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def build_url(site_numbers: Iterable[str], parameter_codes: Iterable[str], period: str) -> str:
    query = urllib.parse.urlencode(
        {
            "format": "json",
            "sites": ",".join(site_numbers),
            "parameterCd": ",".join(parameter_codes),
            "period": period,
            "siteStatus": "all",
        }
    )
    return f"{USGS_IV_ENDPOINT}?{query}"


def fetch_json(url: str, timeout_seconds: int = 30) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "NRHIS/0.1 Build050 (+https://github.com/treycranford75-coder/NRHIS)"
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        if getattr(response, "status", 200) != 200:
            raise HarvestError(f"USGS returned HTTP {response.status}")
        return response.read()


def parse_usgs_payload(
    payload: dict[str, Any], *, now: datetime, stale_minutes: int
) -> list[Observation]:
    try:
        series_list = payload["value"]["timeSeries"]
    except (KeyError, TypeError) as exc:
        raise HarvestError("USGS payload is missing value.timeSeries") from exc

    observations: list[Observation] = []
    for series in series_list:
        source_info = series.get("sourceInfo") or {}
        variable = series.get("variable") or {}
        site_codes = source_info.get("siteCode") or []
        variable_codes = variable.get("variableCode") or []
        values_groups = series.get("values") or []
        if not site_codes or not variable_codes or not values_groups:
            continue

        site_no = str(site_codes[0].get("value", "")).strip()
        site_name = str(source_info.get("siteName", site_no)).strip()
        parameter_code = str(variable_codes[0].get("value", "")).strip()
        parameter_name, fallback_unit = PARAMETERS.get(
            parameter_code,
            (str(variable.get("variableDescription", parameter_code)), ""),
        )
        unit = (
            str((variable.get("unit") or {}).get("unitCode", fallback_unit)).strip()
            or fallback_unit
        )
        values = values_groups[0].get("value") or []
        if not values:
            continue

        latest = max(values, key=lambda item: parse_timestamp(str(item["dateTime"])))
        observed_at = str(latest["dateTime"])
        observed_dt = parse_timestamp(observed_at)
        raw_value = latest.get("value")
        try:
            numeric_value = float(raw_value) if raw_value not in (None, "", "-999999") else None
        except (TypeError, ValueError):
            numeric_value = None
        qualifiers = tuple(str(item) for item in (latest.get("qualifiers") or []))
        provisional = any(item.upper().startswith("P") for item in qualifiers)
        age_minutes = (now - observed_dt).total_seconds() / 60
        stale = age_minutes > stale_minutes
        estimated_tds = None
        if parameter_code == "00095" and numeric_value is not None:
            estimated_tds = round(numeric_value * 0.65, 1)

        observations.append(
            Observation(
                site_no=site_no,
                site_name=site_name,
                parameter_code=parameter_code,
                parameter_name=parameter_name,
                unit=unit,
                observed_at=observed_dt.isoformat().replace("+00:00", "Z"),
                value=numeric_value,
                qualifiers=qualifiers,
                provisional=provisional,
                stale=stale,
                estimated_tds_mg_l=estimated_tds,
            )
        )
    return sorted(observations, key=lambda item: (item.site_no, item.parameter_code))


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def append_deduplicated_jsonl(path: Path, observations: Iterable[Observation]) -> int:
    existing: set[str] = set()
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                item = json.loads(line)
                existing.add(f"{item['site_no']}|{item['parameter_code']}|{item['observed_at']}")
    new_items = [item for item in observations if item.identity not in existing]
    if new_items:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="") as handle:
            for item in new_items:
                handle.write(json.dumps(asdict(item), separators=(",", ":"), sort_keys=True) + "\n")
    return len(new_items)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else ["site_no"]
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


def harvest(
    config_path: Path, output_root: Path, *, period: str = "P2D", timeout_seconds: int = 30
) -> dict[str, Any]:
    config = load_json(config_path)
    sites = config["stations"]
    site_numbers = [str(item["site_no"]) for item in sites]
    parameter_codes = [str(item) for item in config.get("parameter_codes", PARAMETERS)]
    stale_minutes = int(config.get("stale_minutes", 90))
    run_started = utc_now()
    url = build_url(site_numbers, parameter_codes, period)
    raw_bytes = fetch_json(url, timeout_seconds=timeout_seconds)
    payload = json.loads(raw_bytes.decode("utf-8"))
    observations = parse_usgs_payload(payload, now=run_started, stale_minutes=stale_minutes)

    timestamp = run_started.strftime("%Y%m%dT%H%M%SZ")
    raw_path = output_root / "raw" / "usgs_iv" / f"usgs-iv-{timestamp}.json"
    atomic_write_text(raw_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")

    history_path = output_root / "normalized" / "usgs_observations.jsonl"
    appended = append_deduplicated_jsonl(history_path, observations)
    current_rows = [asdict(item) for item in observations]
    for row in current_rows:
        row["qualifiers"] = ";".join(row["qualifiers"])
    current_json = output_root / "current" / "usgs_current_conditions.json"
    current_csv = output_root / "current" / "usgs_current_conditions.csv"
    atomic_write_text(
        current_json,
        json.dumps([asdict(item) for item in observations], indent=2, sort_keys=True) + "\n",
    )
    write_csv(current_csv, current_rows)

    returned_sites = {item.site_no for item in observations}
    status_rows: list[dict[str, Any]] = []
    for station in sites:
        site_no = str(station["site_no"])
        station_obs = [item for item in observations if item.site_no == site_no]
        status_rows.append(
            {
                "site_no": site_no,
                "configured_name": station["name"],
                "observations": len(station_obs),
                "missing": site_no not in returned_sites,
                "stale_parameters": sum(1 for item in station_obs if item.stale),
                "provisional_parameters": sum(1 for item in station_obs if item.provisional),
                "latest_observed_at": max((item.observed_at for item in station_obs), default=""),
            }
        )
    status_csv = output_root / "current" / "usgs_station_status.csv"
    write_csv(status_csv, status_rows)

    receipt = {
        "schema_version": 1,
        "build": "050",
        "started_at": run_started.isoformat().replace("+00:00", "Z"),
        "completed_at": utc_now().isoformat().replace("+00:00", "Z"),
        "request_url": url,
        "configured_sites": len(site_numbers),
        "returned_sites": len(returned_sites),
        "observations": len(observations),
        "new_history_records": appended,
        "stale_observations": sum(1 for item in observations if item.stale),
        "missing_sites": [item["site_no"] for item in status_rows if item["missing"]],
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "files": {
            "raw": str(raw_path),
            "history": str(history_path),
            "current_json": str(current_json),
            "current_csv": str(current_csv),
            "station_status_csv": str(status_csv),
        },
    }
    receipt_path = output_root / "receipts" / f"usgs-harvest-{timestamp}.json"
    atomic_write_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    receipt["receipt_path"] = str(receipt_path)
    return receipt
