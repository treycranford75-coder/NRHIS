"""Bounded-memory query engine for the finalized NRHIS USGS historical CSV archive.

The finalized archive can contain tens of millions of observations and a CSV that is
many gigabytes in size. This module builds a tiny sparse byte-offset index over the
chronologically sorted CSV, then seeks near a requested start time and scans only the
requested window. It never calls USGS and never loads the full archive into memory.
"""

from __future__ import annotations

import bisect
import csv
import hashlib
import json
import os
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence

INDEX_SCHEMA_VERSION = 1
DEFAULT_STRIDE_ROWS = 50_000


class QueryError(RuntimeError):
    """Raised when the local historical archive cannot be queried safely."""


def sha256_file(path: Path, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(block_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


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


def _parse_timestamp(value: str, *, end_boundary: bool = False) -> datetime:
    raw = value.strip()
    if not raw:
        raise QueryError("Timestamp is required")
    try:
        if len(raw) == 10:
            parsed = datetime.combine(date.fromisoformat(raw), datetime.min.time(), tzinfo=timezone.utc)
            if end_boundary:
                parsed += timedelta(days=1)
            return parsed
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise QueryError(f"Invalid ISO timestamp/date: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_window(start: str, end: str) -> tuple[str, str]:
    """Return inclusive start and exclusive end boundaries in UTC.

    Date-only end values are interpreted as the full requested day, so
    ``end=2018-05-12`` becomes an exclusive boundary of 2018-05-13T00:00:00Z.
    Explicit timestamp end values remain exclusive exactly as supplied.
    """

    start_dt = _parse_timestamp(start)
    end_dt = _parse_timestamp(end, end_boundary=len(end.strip()) == 10)
    if end_dt <= start_dt:
        raise QueryError("End boundary must be later than start boundary")
    return _iso_z(start_dt), _iso_z(end_dt)


def _parse_csv_line(raw_line: bytes) -> list[str]:
    try:
        text = raw_line.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise QueryError("Historical CSV contains invalid UTF-8") from exc
    try:
        return next(csv.reader([text]))
    except (csv.Error, StopIteration) as exc:
        raise QueryError("Historical CSV contains an invalid row") from exc


def build_sparse_index(
    csv_path: Path,
    index_path: Path,
    *,
    stride_rows: int = DEFAULT_STRIDE_ROWS,
) -> dict[str, Any]:
    """Build a compact seek index while validating chronological CSV order.

    The index stores only one byte offset every ``stride_rows`` observations. The
    source CSV SHA-256 is computed during the same pass, so the index itself becomes
    a provenance record for the exact finalized archive it describes.
    """

    if stride_rows < 1:
        raise QueryError("stride_rows must be at least 1")
    if not csv_path.is_file():
        raise QueryError(f"Historical CSV does not exist: {csv_path}")

    digest = hashlib.sha256()
    entries: list[dict[str, Any]] = []
    total_rows = 0
    first_observed_at: str | None = None
    last_observed_at: str | None = None
    previous_observed_at: str | None = None

    with csv_path.open("rb") as handle:
        raw_header = handle.readline()
        digest.update(raw_header)
        if not raw_header:
            raise QueryError("Historical CSV is empty")
        header = _parse_csv_line(raw_header)
        try:
            observed_index = header.index("observed_at")
        except ValueError as exc:
            raise QueryError("Historical CSV is missing observed_at") from exc

        while True:
            offset = handle.tell()
            raw_line = handle.readline()
            if not raw_line:
                break
            digest.update(raw_line)
            if not raw_line.strip():
                continue
            values = _parse_csv_line(raw_line)
            if len(values) != len(header):
                raise QueryError(
                    f"Historical CSV row {total_rows + 2} has {len(values)} fields; "
                    f"expected {len(header)}"
                )
            observed_at = values[observed_index]
            if previous_observed_at is not None and observed_at < previous_observed_at:
                raise QueryError(
                    "Historical CSV is not globally sorted by observed_at; "
                    f"row {total_rows + 2} regressed from {previous_observed_at} to {observed_at}"
                )
            if first_observed_at is None:
                first_observed_at = observed_at
            if total_rows % stride_rows == 0:
                entries.append(
                    {
                        "row_number": total_rows + 1,
                        "observed_at": observed_at,
                        "byte_offset": offset,
                    }
                )
            previous_observed_at = observed_at
            last_observed_at = observed_at
            total_rows += 1

    payload: dict[str, Any] = {
        "schema_version": INDEX_SCHEMA_VERSION,
        "created_at": _iso_z(datetime.now(timezone.utc)),
        "source_csv": str(csv_path.resolve()),
        "source_csv_bytes": csv_path.stat().st_size,
        "source_csv_sha256": digest.hexdigest(),
        "stride_rows": stride_rows,
        "total_rows": total_rows,
        "first_observed_at": first_observed_at,
        "last_observed_at": last_observed_at,
        "entries": entries,
    }
    atomic_write_text(index_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    payload["index_path"] = str(index_path.resolve())
    payload["index_sha256"] = sha256_file(index_path)
    return payload


def load_sparse_index(index_path: Path, csv_path: Path) -> dict[str, Any]:
    if not index_path.is_file():
        raise QueryError(f"Sparse index does not exist: {index_path}")
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QueryError(f"Unable to read sparse index: {index_path}") from exc
    if payload.get("schema_version") != INDEX_SCHEMA_VERSION:
        raise QueryError("Unsupported historical query index schema")
    if not csv_path.is_file():
        raise QueryError(f"Historical CSV does not exist: {csv_path}")
    if int(payload.get("source_csv_bytes", -1)) != csv_path.stat().st_size:
        raise QueryError("Historical CSV size changed after the sparse index was built")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise QueryError("Sparse index entries are missing")
    return payload


def _seek_offset(index: dict[str, Any], start_iso: str) -> int | None:
    entries = index.get("entries") or []
    if not entries:
        return None
    timestamps = [str(entry["observed_at"]) for entry in entries]
    position = bisect.bisect_right(timestamps, start_iso) - 1
    if position < 0:
        return int(entries[0]["byte_offset"])
    return int(entries[position]["byte_offset"])


def query_history(
    csv_path: Path,
    index_path: Path,
    *,
    start: str,
    end: str,
    site_nos: Sequence[str] | None = None,
    parameter_codes: Sequence[str] | None = None,
    limit: int | None = None,
) -> Iterator[dict[str, str]]:
    """Yield rows from the finalized local archive for an evidentiary time window."""

    if limit is not None and limit < 1:
        raise QueryError("limit must be at least 1 when supplied")
    start_iso, end_exclusive = normalize_window(start, end)
    index = load_sparse_index(index_path, csv_path)
    offset = _seek_offset(index, start_iso)
    site_filter = {str(value) for value in site_nos or []}
    parameter_filter = {str(value) for value in parameter_codes or []}

    yielded = 0
    with csv_path.open("rb") as handle:
        raw_header = handle.readline()
        header = _parse_csv_line(raw_header)
        try:
            observed_index = header.index("observed_at")
            site_index = header.index("site_no")
            parameter_index = header.index("parameter_code")
        except ValueError as exc:
            raise QueryError("Historical CSV is missing required query fields") from exc
        if offset is not None:
            handle.seek(offset)

        while True:
            raw_line = handle.readline()
            if not raw_line:
                break
            if not raw_line.strip():
                continue
            values = _parse_csv_line(raw_line)
            if len(values) != len(header):
                raise QueryError("Historical CSV contains a malformed row in the query window")
            observed_at = values[observed_index]
            if observed_at < start_iso:
                continue
            if observed_at >= end_exclusive:
                break
            if site_filter and values[site_index] not in site_filter:
                continue
            if parameter_filter and values[parameter_index] not in parameter_filter:
                continue
            yield dict(zip(header, values, strict=True))
            yielded += 1
            if limit is not None and yielded >= limit:
                return


def write_query_bundle(
    csv_path: Path,
    index_path: Path,
    output_dir: Path,
    *,
    start: str,
    end: str,
    site_nos: Sequence[str] | None = None,
    parameter_codes: Sequence[str] | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Write a small evidence CSV and provenance receipt for a local-only query."""

    index = load_sparse_index(index_path, csv_path)
    start_iso, end_exclusive = normalize_window(start, end)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = output_dir / "observations.csv"
    receipt_path = output_dir / "query-receipt.json"

    rows = query_history(
        csv_path,
        index_path,
        start=start,
        end=end,
        site_nos=site_nos,
        parameter_codes=parameter_codes,
        limit=limit,
    )

    count = 0
    first_observed_at: str | None = None
    last_observed_at: str | None = None
    fields: list[str] | None = None
    fd, temp_name = tempfile.mkstemp(prefix=output_csv.name, suffix=".tmp", dir=output_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer: csv.DictWriter[str] | None = None
            for row in rows:
                if fields is None:
                    fields = list(row.keys())
                    writer = csv.DictWriter(handle, fieldnames=fields)
                    writer.writeheader()
                assert writer is not None
                writer.writerow(row)
                observed_at = row["observed_at"]
                if first_observed_at is None:
                    first_observed_at = observed_at
                last_observed_at = observed_at
                count += 1
            if writer is None:
                fields = [
                    "estimated_tds_mg_l",
                    "observed_at",
                    "parameter_code",
                    "parameter_name",
                    "provisional",
                    "qualifiers",
                    "site_name",
                    "site_no",
                    "source",
                    "unit",
                    "value",
                ]
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
        os.replace(temp_name, output_csv)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)

    receipt: dict[str, Any] = {
        "schema_version": 1,
        "build": "095",
        "created_at": _iso_z(datetime.now(timezone.utc)),
        "query_mode": "local_finalized_archive",
        "network_requests_made": 0,
        "source_csv": str(csv_path.resolve()),
        "source_csv_bytes": int(index["source_csv_bytes"]),
        "source_csv_sha256": str(index["source_csv_sha256"]),
        "query_index": str(index_path.resolve()),
        "query_index_sha256": sha256_file(index_path),
        "requested_start": start,
        "requested_end": end,
        "effective_start": start_iso,
        "effective_end_exclusive": end_exclusive,
        "site_nos": list(site_nos or []),
        "parameter_codes": list(parameter_codes or []),
        "limit": limit,
        "result_count": count,
        "first_observed_at": first_observed_at,
        "last_observed_at": last_observed_at,
        "output_csv": str(output_csv.resolve()),
        "output_csv_bytes": output_csv.stat().st_size,
        "output_csv_sha256": sha256_file(output_csv),
    }
    atomic_write_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    receipt["receipt"] = str(receipt_path.resolve())
    return receipt
