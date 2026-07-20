"""Incremental USGS update and basin data-quality assessment for NRHIS Build052."""
from __future__ import annotations

import csv
import json
import os
import tempfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from nrhis_harvest.usgs_historical_backfill import backfill, parse_iso_date, parse_timestamp


class IncrementalUpdateError(RuntimeError):
    """Raised when incremental update state is invalid."""


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


def _load_history(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise IncrementalUpdateError(f"Invalid history JSONL at line {line_number}") from exc
    return rows


def latest_history_date(history_path: Path) -> date | None:
    latest: datetime | None = None
    for row in _load_history(history_path):
        observed = parse_timestamp(str(row["observed_at"]))
        if latest is None or observed > latest:
            latest = observed
    return latest.date() if latest else None


def choose_incremental_start(
    history_path: Path,
    *,
    study_start: date,
    end_date: date,
    overlap_days: int,
) -> date:
    if overlap_days < 0:
        raise IncrementalUpdateError("overlap_days cannot be negative")
    latest = latest_history_date(history_path)
    if latest is None:
        return study_start
    candidate = latest - timedelta(days=overlap_days)
    return max(study_start, min(candidate, end_date))


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


def build_quality_summary(
    config_path: Path,
    history_path: Path,
    output_root: Path,
    *,
    assessed_at: datetime,
    lookback_days: int = 7,
    gap_minutes: int = 120,
    stale_minutes: int = 90,
) -> dict[str, Any]:
    if lookback_days < 1 or gap_minutes < 1 or stale_minutes < 1:
        raise IncrementalUpdateError("quality thresholds must be positive")

    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    rows = _load_history(history_path)
    cutoff = assessed_at - timedelta(days=lookback_days)
    recent = [row for row in rows if parse_timestamp(str(row["observed_at"])) >= cutoff]

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in recent:
        grouped[(str(row["site_no"]), str(row["parameter_code"]))].append(row)

    gap_rows: list[dict[str, Any]] = []
    parameter_status: list[dict[str, Any]] = []
    for station in config["stations"]:
        site_no = str(station["site_no"])
        for parameter_code in config.get("parameter_codes", []):
            key = (site_no, str(parameter_code))
            observations = sorted(grouped.get(key, []), key=lambda row: row["observed_at"])
            latest = parse_timestamp(str(observations[-1]["observed_at"])) if observations else None
            age_minutes = round((assessed_at - latest).total_seconds() / 60, 1) if latest else None
            stale = latest is None or age_minutes is None or age_minutes > stale_minutes
            gap_count = 0
            for previous, current in zip(observations, observations[1:]):
                previous_dt = parse_timestamp(str(previous["observed_at"]))
                current_dt = parse_timestamp(str(current["observed_at"]))
                duration = (current_dt - previous_dt).total_seconds() / 60
                if duration > gap_minutes:
                    gap_count += 1
                    gap_rows.append(
                        {
                            "site_no": site_no,
                            "station_name": station["name"],
                            "parameter_code": parameter_code,
                            "gap_start": previous_dt.isoformat().replace("+00:00", "Z"),
                            "gap_end": current_dt.isoformat().replace("+00:00", "Z"),
                            "gap_minutes": round(duration, 1),
                        }
                    )
            parameter_status.append(
                {
                    "site_no": site_no,
                    "station_name": station["name"],
                    "parameter_code": str(parameter_code),
                    "observations_in_window": len(observations),
                    "latest_observed_at": latest.isoformat().replace("+00:00", "Z") if latest else "",
                    "age_minutes": age_minutes,
                    "missing": not observations,
                    "stale": stale,
                    "gap_count": gap_count,
                }
            )

    summary = {
        "schema_version": 1,
        "build": "052",
        "assessed_at": assessed_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "lookback_days": lookback_days,
        "gap_minutes": gap_minutes,
        "stale_minutes": stale_minutes,
        "configured_station_parameters": len(parameter_status),
        "missing_station_parameters": sum(1 for row in parameter_status if row["missing"]),
        "stale_station_parameters": sum(1 for row in parameter_status if row["stale"]),
        "detected_gaps": len(gap_rows),
        "ready_for_reporting": not any(row["missing"] or row["stale"] for row in parameter_status),
        "parameter_status": parameter_status,
    }

    quality_dir = output_root / "quality"
    _atomic_write(quality_dir / "usgs_data_quality_summary.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    _write_csv(
        quality_dir / "usgs_parameter_status.csv",
        parameter_status,
        [
            "site_no",
            "station_name",
            "parameter_code",
            "observations_in_window",
            "latest_observed_at",
            "age_minutes",
            "missing",
            "stale",
            "gap_count",
        ],
    )
    _write_csv(
        quality_dir / "usgs_detected_gaps.csv",
        gap_rows,
        ["site_no", "station_name", "parameter_code", "gap_start", "gap_end", "gap_minutes"],
    )
    return summary


def incremental_update(
    config_path: Path,
    output_root: Path,
    *,
    end_date: str,
    study_start: str = "2024-02-01",
    overlap_days: int = 2,
    chunk_days: int = 2,
    timeout_seconds: int = 60,
    lookback_days: int = 7,
    gap_minutes: int = 120,
    assessed_at: datetime | None = None,
) -> dict[str, Any]:
    end = parse_iso_date(end_date)
    start_floor = parse_iso_date(study_start)
    history_path = output_root / "historical" / "usgs_observations_history.jsonl"
    start = choose_incremental_start(
        history_path,
        study_start=start_floor,
        end_date=end,
        overlap_days=overlap_days,
    )
    backfill_receipt = backfill(
        config_path,
        output_root,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        chunk_days=chunk_days,
        timeout_seconds=timeout_seconds,
        resume=True,
    )
    now = assessed_at or datetime.now(timezone.utc)
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    quality = build_quality_summary(
        config_path,
        history_path,
        output_root,
        assessed_at=now,
        lookback_days=lookback_days,
        gap_minutes=gap_minutes,
        stale_minutes=int(config.get("stale_minutes", 90)),
    )
    receipt = {
        "schema_version": 1,
        "build": "052",
        "incremental_start": start.isoformat(),
        "incremental_end": end.isoformat(),
        "overlap_days": overlap_days,
        "backfill": backfill_receipt,
        "quality": {
            "ready_for_reporting": quality["ready_for_reporting"],
            "missing_station_parameters": quality["missing_station_parameters"],
            "stale_station_parameters": quality["stale_station_parameters"],
            "detected_gaps": quality["detected_gaps"],
        },
    }
    receipt_path = output_root / "receipts" / "usgs_incremental_update_receipt.json"
    _atomic_write(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    receipt["receipt_path"] = str(receipt_path)
    return receipt
