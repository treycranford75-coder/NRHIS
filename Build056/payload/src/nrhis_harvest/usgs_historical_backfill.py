"""Restart-safe historical USGS Instantaneous Values backfill for NRHIS.

Build052 extends the production current-condition harvester with chunked date-range
retrieval. It uses only the Python standard library, archives each upstream response,
keeps an append-only duplicate-safe history, and records a resumable checkpoint.
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
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

USGS_IV_ENDPOINT = "https://waterservices.usgs.gov/nwis/iv/"
PARAMETERS = {
    "00060": ("discharge", "ft3/s"),
    "00065": ("gage_height", "ft"),
    "00010": ("water_temperature", "degC"),
    "00095": ("specific_conductance", "uS/cm"),
}


class BackfillError(RuntimeError):
    """Raised when a historical response cannot be safely processed."""


@dataclass(frozen=True)
class HistoricalObservation:
    site_no: str
    site_name: str
    parameter_code: str
    parameter_name: str
    unit: str
    observed_at: str
    value: float | None
    qualifiers: tuple[str, ...]
    provisional: bool
    estimated_tds_mg_l: float | None
    source: str = "USGS Instantaneous Values API"

    @property
    def identity(self) -> str:
        return f"{self.site_no}|{self.parameter_code}|{self.observed_at}"


def parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise BackfillError(f"Invalid ISO date: {value}") from exc


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iter_date_chunks(start: date, end: date, chunk_days: int) -> Iterator[tuple[date, date]]:
    if chunk_days < 1:
        raise BackfillError("chunk_days must be at least 1")
    if end < start:
        raise BackfillError("end date precedes start date")
    cursor = start
    while cursor <= end:
        chunk_end = min(cursor + timedelta(days=chunk_days - 1), end)
        yield cursor, chunk_end
        cursor = chunk_end + timedelta(days=1)


def build_url(
    site_numbers: Iterable[str],
    parameter_codes: Iterable[str],
    start: date,
    end: date,
) -> str:
    query = urllib.parse.urlencode(
        {
            "format": "json",
            "sites": ",".join(site_numbers),
            "parameterCd": ",".join(parameter_codes),
            "startDT": start.isoformat(),
            "endDT": end.isoformat(),
            "siteStatus": "all",
        }
    )
    return f"{USGS_IV_ENDPOINT}?{query}"


def fetch_json(url: str, timeout_seconds: int = 60) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "NRHIS/0.1 Build052 (+https://github.com/treycranford75-coder/NRHIS)"
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        if getattr(response, "status", 200) != 200:
            raise BackfillError(f"USGS returned HTTP {response.status}")
        return response.read()


def parse_payload(payload: dict[str, Any]) -> list[HistoricalObservation]:
    try:
        series_list = payload["value"]["timeSeries"]
    except (KeyError, TypeError) as exc:
        raise BackfillError("USGS payload is missing value.timeSeries") from exc

    records: list[HistoricalObservation] = []
    for series in series_list:
        source_info = series.get("sourceInfo") or {}
        variable = series.get("variable") or {}
        site_codes = source_info.get("siteCode") or []
        variable_codes = variable.get("variableCode") or []
        if not site_codes or not variable_codes:
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
        for group in series.get("values") or []:
            for item in group.get("value") or []:
                observed_at = (
                    parse_timestamp(str(item["dateTime"])).isoformat().replace("+00:00", "Z")
                )
                raw_value = item.get("value")
                try:
                    value = float(raw_value) if raw_value not in (None, "", "-999999") else None
                except (TypeError, ValueError):
                    value = None
                qualifiers = tuple(str(q) for q in (item.get("qualifiers") or []))
                provisional = any(q.upper().startswith("P") for q in qualifiers)
                estimated_tds = None
                if parameter_code == "00095" and value is not None:
                    estimated_tds = round(value * 0.65, 1)
                records.append(
                    HistoricalObservation(
                        site_no=site_no,
                        site_name=site_name,
                        parameter_code=parameter_code,
                        parameter_name=parameter_name,
                        unit=unit,
                        observed_at=observed_at,
                        value=value,
                        qualifiers=qualifiers,
                        provisional=provisional,
                        estimated_tds_mg_l=estimated_tds,
                    )
                )
    records.sort(key=lambda r: (r.observed_at, r.site_no, r.parameter_code))
    return records


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


def existing_identities(path: Path) -> set[str]:
    identities: set[str] = set()
    if not path.exists():
        return identities
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            identities.add(f"{row['site_no']}|{row['parameter_code']}|{row['observed_at']}")
    return identities


def append_deduplicated(path: Path, records: Iterable[HistoricalObservation]) -> int:
    known = existing_identities(path)
    new_records = [record for record in records if record.identity not in known]
    if new_records:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="") as handle:
            for record in new_records:
                handle.write(
                    json.dumps(asdict(record), sort_keys=True, separators=(",", ":")) + "\n"
                )
    return len(new_records)


def rebuild_csv(history_path: Path, csv_path: Path) -> int:
    rows: list[dict[str, Any]] = []
    if history_path.exists():
        with history_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    row["qualifiers"] = ";".join(row.get("qualifiers") or [])
                    rows.append(row)
    rows.sort(key=lambda row: (row["observed_at"], row["site_no"], row["parameter_code"]))
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else ["site_no"]
    fd, temp_name = tempfile.mkstemp(prefix=csv_path.name, suffix=".tmp", dir=csv_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temp_name, csv_path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return len(rows)


def backfill(
    config_path: Path,
    output_root: Path,
    *,
    start_date: str,
    end_date: str,
    chunk_days: int = 7,
    timeout_seconds: int = 60,
    resume: bool = True,
) -> dict[str, Any]:
    config = load_json(config_path)
    sites = [str(station["site_no"]) for station in config["stations"]]
    parameters = [str(code) for code in config.get("parameter_codes", PARAMETERS)]
    requested_start = parse_iso_date(start_date)
    requested_end = parse_iso_date(end_date)
    checkpoint_path = output_root / "backfill" / "checkpoint.json"
    effective_start = requested_start
    if resume and checkpoint_path.exists():
        checkpoint = load_json(checkpoint_path)
        if checkpoint.get("completed_through"):
            candidate = parse_iso_date(str(checkpoint["completed_through"])) + timedelta(days=1)
            if candidate > effective_start:
                effective_start = candidate

    history_path = output_root / "normalized" / "usgs_historical_observations.jsonl"
    csv_path = output_root / "normalized" / "usgs_historical_observations.csv"
    run_started = datetime.now(timezone.utc)
    chunk_receipts: list[dict[str, Any]] = []
    new_records_total = 0
    chunks_completed = 0

    if effective_start <= requested_end:
        for chunk_start, chunk_end in iter_date_chunks(effective_start, requested_end, chunk_days):
            url = build_url(sites, parameters, chunk_start, chunk_end)
            raw = fetch_json(url, timeout_seconds=timeout_seconds)
            payload = json.loads(raw.decode("utf-8"))
            records = parse_payload(payload)
            raw_path = (
                output_root / "raw" / "usgs_iv_backfill" / f"usgs-iv-{chunk_start}-{chunk_end}.json"
            )
            atomic_write_text(raw_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
            new_records = append_deduplicated(history_path, records)
            new_records_total += new_records
            chunks_completed += 1
            chunk_receipts.append(
                {
                    "start": chunk_start.isoformat(),
                    "end": chunk_end.isoformat(),
                    "request_url": url,
                    "records_received": len(records),
                    "new_records": new_records,
                    "raw_file": str(raw_path),
                    "raw_sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
            atomic_write_text(
                checkpoint_path,
                json.dumps(
                    {
                        "schema_version": 1,
                        "build": "052",
                        "requested_start": requested_start.isoformat(),
                        "requested_end": requested_end.isoformat(),
                        "completed_through": chunk_end.isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
            )

    total_history_records = rebuild_csv(history_path, csv_path)
    receipt = {
        "schema_version": 1,
        "build": "052",
        "started_at": run_started.isoformat().replace("+00:00", "Z"),
        "completed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "requested_start": requested_start.isoformat(),
        "requested_end": requested_end.isoformat(),
        "effective_start": effective_start.isoformat(),
        "chunk_days": chunk_days,
        "chunks_completed": chunks_completed,
        "new_records": new_records_total,
        "total_history_records": total_history_records,
        "checkpoint": str(checkpoint_path),
        "history_jsonl": str(history_path),
        "history_csv": str(csv_path),
        "chunks": chunk_receipts,
    }
    receipt_path = (
        output_root / "receipts" / f"usgs-backfill-{run_started.strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    atomic_write_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    receipt["receipt"] = str(receipt_path)
    return receipt
