from __future__ import annotations

from pathlib import Path


def main() -> int:
    repo = Path.cwd()
    target = repo / "src" / "nrhis_harvest" / "usgs_historical_backfill.py"
    if not target.is_file():
        raise SystemExit(f"Missing target module: {target}")

    text = target.read_text(encoding="utf-8")

    if "import heapq" not in text:
        text = text.replace("import hashlib\n", "import hashlib\nimport heapq\n", 1)
    if "import sqlite3" not in text:
        text = text.replace("import os\n", "import os\nimport sqlite3\n", 1)

    rebuild_start = text.find("def rebuild_csv(history_path: Path, csv_path: Path) -> int:\n")
    backfill_start = text.find("def backfill(\n", rebuild_start)
    if rebuild_start < 0 or backfill_start < 0:
        raise SystemExit("Unable to locate rebuild_csv/backfill boundary.")

    replacement = r'''IDENTITY_INDEX_BATCH_SIZE = 10000
CSV_SORT_CHUNK_ROWS = 50000


def _identity_from_row(row: dict[str, Any]) -> str:
    return f"{row['site_no']}|{row['parameter_code']}|{row['observed_at']}"


def _metadata_int(connection: sqlite3.Connection, key: str, default: int = 0) -> int:
    row = connection.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
    if row is None:
        return default
    try:
        return int(row[0])
    except (TypeError, ValueError):
        return default


def _set_metadata(connection: sqlite3.Connection, key: str, value: int | str) -> None:
    connection.execute(
        "INSERT INTO metadata(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, str(value)),
    )


def identity_index_count(connection: sqlite3.Connection) -> int:
    return int(connection.execute("SELECT COUNT(*) FROM identities").fetchone()[0])


def sync_identity_index(
    connection: sqlite3.Connection,
    history_path: Path,
    *,
    batch_size: int = IDENTITY_INDEX_BATCH_SIZE,
) -> int:
    """Synchronize a disk-backed identity index with the append-only JSONL archive."""
    current_size = history_path.stat().st_size if history_path.exists() else 0
    indexed_bytes = _metadata_int(connection, "indexed_bytes")

    if indexed_bytes > current_size:
        with connection:
            connection.execute("DELETE FROM identities")
            _set_metadata(connection, "indexed_bytes", 0)
        indexed_bytes = 0

    if current_size == 0:
        if indexed_bytes != 0 or identity_index_count(connection) != 0:
            with connection:
                connection.execute("DELETE FROM identities")
                _set_metadata(connection, "indexed_bytes", 0)
        return 0

    if indexed_bytes == current_size:
        return identity_index_count(connection)

    batch: list[tuple[str]] = []
    last_complete_offset = indexed_bytes
    with history_path.open("rb") as handle:
        handle.seek(indexed_bytes)
        while True:
            line_offset = handle.tell()
            raw_line = handle.readline()
            if not raw_line:
                break
            last_complete_offset = handle.tell()
            if not raw_line.strip():
                continue
            try:
                row = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise BackfillError(
                    f"Historical JSONL contains invalid JSON at byte offset {line_offset}"
                ) from exc
            batch.append((_identity_from_row(row),))
            if len(batch) >= batch_size:
                with connection:
                    connection.executemany(
                        "INSERT OR IGNORE INTO identities(identity) VALUES(?)",
                        batch,
                    )
                    _set_metadata(connection, "indexed_bytes", last_complete_offset)
                batch.clear()

    with connection:
        if batch:
            connection.executemany(
                "INSERT OR IGNORE INTO identities(identity) VALUES(?)",
                batch,
            )
        _set_metadata(connection, "indexed_bytes", current_size)

    return identity_index_count(connection)


def open_identity_index(index_path: Path, history_path: Path) -> sqlite3.Connection:
    """Open and synchronize the persistent SQLite identity index."""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(index_path)
    connection.execute("PRAGMA synchronous=NORMAL")
    connection.execute(
        "CREATE TABLE IF NOT EXISTS identities(identity TEXT PRIMARY KEY)"
    )
    connection.execute(
        "CREATE TABLE IF NOT EXISTS metadata("
        "key TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
    connection.commit()
    sync_identity_index(connection, history_path)
    return connection


def append_deduplicated_indexed(
    path: Path,
    records: Iterable[HistoricalObservation],
    connection: sqlite3.Connection,
) -> int:
    """Append only identities absent from SQLite while keeping JSONL/index restart-safe."""
    new_records: list[HistoricalObservation] = []
    try:
        connection.execute("BEGIN")
        for record in records:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO identities(identity) VALUES(?)",
                (record.identity,),
            )
            if cursor.rowcount == 1:
                new_records.append(record)

        if new_records:
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = "".join(
                json.dumps(asdict(record), sort_keys=True, separators=(",", ":")) + "\n"
                for record in new_records
            )
            with path.open("a", encoding="utf-8", newline="") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())

        indexed_bytes = path.stat().st_size if path.exists() else 0
        _set_metadata(connection, "indexed_bytes", indexed_bytes)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return len(new_records)


def _row_sort_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (str(row["observed_at"]), str(row["site_no"]), str(row["parameter_code"]))


def _iter_sorted_rows(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def rebuild_csv(
    history_path: Path,
    csv_path: Path,
    *,
    sort_chunk_rows: int = CSV_SORT_CHUNK_ROWS,
) -> int:
    """Externally sort JSONL and write CSV with bounded memory usage."""
    if sort_chunk_rows < 1:
        raise BackfillError("sort_chunk_rows must be at least 1")

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] | None = None
    total_rows = 0

    with tempfile.TemporaryDirectory(prefix="usgs-csv-sort-", dir=csv_path.parent) as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        chunk_paths: list[Path] = []
        chunk: list[dict[str, Any]] = []

        if history_path.exists():
            with history_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    if fieldnames is None:
                        fieldnames = list(row.keys())
                    chunk.append(row)
                    if len(chunk) >= sort_chunk_rows:
                        chunk.sort(key=_row_sort_key)
                        chunk_path = temp_dir / f"chunk-{len(chunk_paths):06d}.jsonl"
                        with chunk_path.open("w", encoding="utf-8", newline="") as chunk_handle:
                            for item in chunk:
                                chunk_handle.write(
                                    json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n"
                                )
                        chunk_paths.append(chunk_path)
                        chunk.clear()

        if chunk:
            chunk.sort(key=_row_sort_key)
            chunk_path = temp_dir / f"chunk-{len(chunk_paths):06d}.jsonl"
            with chunk_path.open("w", encoding="utf-8", newline="") as chunk_handle:
                for item in chunk:
                    chunk_handle.write(json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n")
            chunk_paths.append(chunk_path)
            chunk.clear()

        if fieldnames is None:
            fieldnames = ["site_no"]

        fd, temp_name = tempfile.mkstemp(prefix=csv_path.name, suffix=".tmp", dir=csv_path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                if chunk_paths:
                    iterators = [_iter_sorted_rows(path) for path in chunk_paths]
                    for row in heapq.merge(*iterators, key=_row_sort_key):
                        row = dict(row)
                        row["qualifiers"] = ";".join(row.get("qualifiers") or [])
                        writer.writerow(row)
                        total_rows += 1
            os.replace(temp_name, csv_path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    return total_rows


def sha256_file(path: Path, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(block_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def finalize_completed_archive(
    output_root: Path,
    *,
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    """Finalize an already-complete harvest without making any USGS requests."""
    requested_start = parse_iso_date(start_date)
    requested_end = parse_iso_date(end_date)
    checkpoint_path = output_root / "backfill" / "checkpoint.json"
    history_path = output_root / "normalized" / "usgs_historical_observations.jsonl"
    csv_path = output_root / "normalized" / "usgs_historical_observations.csv"
    identity_index_path = output_root / "backfill" / "identity_index.sqlite"

    if not checkpoint_path.exists():
        raise BackfillError(f"Finalization requires checkpoint: {checkpoint_path}")
    if not history_path.exists():
        raise BackfillError(f"Finalization requires historical JSONL: {history_path}")

    checkpoint = load_json(checkpoint_path)
    if str(checkpoint.get("requested_start")) != requested_start.isoformat():
        raise BackfillError("Checkpoint requested_start does not match finalization start date")
    if str(checkpoint.get("requested_end")) != requested_end.isoformat():
        raise BackfillError("Checkpoint requested_end does not match finalization end date")
    completed_raw = checkpoint.get("completed_through")
    if not completed_raw or parse_iso_date(str(completed_raw)) < requested_end:
        raise BackfillError("Checkpoint does not show the requested archive range as complete")

    run_started = datetime.now(timezone.utc)
    identity_index = open_identity_index(identity_index_path, history_path)
    try:
        indexed_identities = identity_index_count(identity_index)
    finally:
        identity_index.close()

    total_history_records = rebuild_csv(history_path, csv_path)
    receipt = {
        "schema_version": 2,
        "build": "094",
        "finalize_only": True,
        "usgs_requests_made": 0,
        "started_at": run_started.isoformat().replace("+00:00", "Z"),
        "completed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "requested_start": requested_start.isoformat(),
        "requested_end": requested_end.isoformat(),
        "completed_through": str(completed_raw),
        "total_history_records": total_history_records,
        "identity_index_final_size": indexed_identities,
        "duplicate_lines_detected": max(0, total_history_records - indexed_identities),
        "checkpoint": str(checkpoint_path),
        "history_jsonl": str(history_path),
        "history_jsonl_bytes": history_path.stat().st_size,
        "history_jsonl_sha256": sha256_file(history_path),
        "history_csv": str(csv_path),
        "history_csv_bytes": csv_path.stat().st_size,
        "history_csv_sha256": sha256_file(csv_path),
        "identity_index": str(identity_index_path),
        "dedupe_backend": "sqlite",
        "csv_sort": "external_merge_sort",
    }
    receipt_path = (
        output_root
        / "receipts"
        / f"usgs-backfill-finalize-{run_started.strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    atomic_write_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    receipt["receipt"] = str(receipt_path)
    return receipt


'''
    text = text[:rebuild_start] + replacement + text[backfill_start:]

    old_identity = '''    history_path = output_root / "normalized" / "usgs_historical_observations.jsonl"\n    csv_path = output_root / "normalized" / "usgs_historical_observations.csv"\n    known_identities = existing_identities(history_path)\n    existing_records_at_start = len(known_identities)\n'''
    new_identity = '''    history_path = output_root / "normalized" / "usgs_historical_observations.jsonl"\n    csv_path = output_root / "normalized" / "usgs_historical_observations.csv"\n    identity_index_path = output_root / "backfill" / "identity_index.sqlite"\n    identity_index = open_identity_index(identity_index_path, history_path)\n    existing_records_at_start = identity_index_count(identity_index)\n'''
    if old_identity not in text:
        raise SystemExit("Unable to locate in-memory identity initialization block.")
    text = text.replace(old_identity, new_identity, 1)

    old_append = "            new_records = append_deduplicated(history_path, records, known_identities)\n"
    new_append = "            new_records = append_deduplicated_indexed(history_path, records, identity_index)\n"
    if old_append not in text:
        raise SystemExit("Unable to locate in-memory append call.")
    text = text.replace(old_append, new_append, 1)

    receipt_old = '        "identity_index_final_size": len(known_identities),\n'
    receipt_new = (
        '        "identity_index_final_size": identity_index_count(identity_index),\n'
        '        "identity_index": str(identity_index_path),\n'
        '        "dedupe_backend": "sqlite",\n'
    )
    backfill_position = text.find("def backfill(\n")
    receipt_position = text.find(receipt_old, backfill_position)
    if receipt_position < 0:
        raise SystemExit("Unable to locate backfill identity receipt field.")
    text = text[:receipt_position] + receipt_new + text[receipt_position + len(receipt_old):]
    if "len(known_identities)" in text[backfill_position:]:
        raise SystemExit("In-memory identity receipt reference remains in backfill.")

    old_tail = '''    atomic_write_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\\n")\n    receipt["receipt"] = str(receipt_path)\n    return receipt\n'''
    new_tail = '''    atomic_write_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\\n")\n    identity_index.close()\n    receipt["receipt"] = str(receipt_path)\n    return receipt\n'''
    tail_position = text.find(old_tail, backfill_position)
    if tail_position < 0:
        raise SystemExit("Unable to locate backfill receipt tail.")
    text = text[:tail_position] + new_tail + text[tail_position + len(old_tail):]

    target.write_text(text, encoding="utf-8", newline="\n")
    print(f"Patched: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
