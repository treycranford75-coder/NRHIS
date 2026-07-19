"""Orchestration for an auditable USGS harvest run."""

from __future__ import annotations

import csv
import hashlib
import json
import logging
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import requests

from .models import HarvestResult
from .registry import load_station_registry
from .usgs import NWIS_IV_URL, build_query, download, normalize

LOGGER = logging.getLogger(__name__)
CSV_FIELDS = (
    "station_id",
    "agency",
    "agency_id",
    "station_name",
    "waterbody",
    "role",
    "parameter",
    "parameter_code",
    "unit",
    "observed_at",
    "value",
    "qualifiers",
    "source",
)


def _canonical_json(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def _write_json(path: Path, payload: Any) -> str:
    encoded = _canonical_json(payload)
    path.write_bytes(encoded + b"\n")
    return hashlib.sha256(encoded).hexdigest()


def harvest_usgs(
    registry_path: Path,
    output_root: Path,
    start: date,
    end: date,
    *,
    session: requests.Session | None = None,
    timeout_seconds: int = 60,
    now: datetime | None = None,
) -> HarvestResult:
    """Harvest, archive, normalize, and document USGS observations."""
    if end < start:
        raise ValueError("end date must be on or after start date")
    stations = load_station_registry(registry_path)
    clock = now or datetime.now(UTC)
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=UTC)
    run_id = clock.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    raw_dir = output_root / "raw" / "usgs" / run_id
    processed_dir = output_root / "processed" / "usgs" / run_id
    raw_dir.mkdir(parents=True, exist_ok=False)
    processed_dir.mkdir(parents=True, exist_ok=False)

    query = build_query(stations, start, end)
    owned_session = session is None
    active_session = session or requests.Session()
    try:
        payload, request_url = download(active_session, query, timeout_seconds)
    finally:
        if owned_session:
            active_session.close()

    raw_path = raw_dir / "nwis_iv.json"
    raw_sha256 = _write_json(raw_path, payload)
    records = normalize(payload, stations)
    normalized_path = processed_dir / "observations.csv"
    with normalized_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    normalized_sha256 = hashlib.sha256(normalized_path.read_bytes()).hexdigest()

    metadata = {
        "schema_version": 1,
        "run_id": run_id,
        "started_at_utc": clock.astimezone(UTC).isoformat(),
        "source": {
            "provider": "U.S. Geological Survey",
            "service": "NWIS Instantaneous Values",
            "endpoint": NWIS_IV_URL,
            "request_url": request_url,
            "query": query,
        },
        "registry": {
            "path": str(registry_path),
            "sha256": hashlib.sha256(registry_path.read_bytes()).hexdigest(),
        },
        "coverage": {"start_date": start.isoformat(), "end_date": end.isoformat()},
        "counts": {"stations": len(stations), "observations": len(records)},
        "artifacts": {
            "raw_json": {"path": str(raw_path), "sha256": raw_sha256},
            "normalized_csv": {"path": str(normalized_path), "sha256": normalized_sha256},
        },
    }
    metadata_path = processed_dir / "metadata.json"
    _write_json(metadata_path, metadata)
    LOGGER.info(
        "USGS harvest complete run_id=%s stations=%d observations=%d",
        run_id,
        len(stations),
        len(records),
    )
    return HarvestResult(
        run_id=run_id,
        raw_path=raw_path,
        normalized_path=normalized_path,
        metadata_path=metadata_path,
        station_count=len(stations),
        observation_count=len(records),
    )
