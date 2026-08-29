from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from nrhis_harvest import usgs_historical_backfill as history


def _record(site: str, parameter: str, when: str, value: float) -> history.HistoricalObservation:
    parameter_name, unit = history.PARAMETERS[parameter]
    return history.HistoricalObservation(
        site_no=site,
        site_name=f"Site {site}",
        parameter_code=parameter,
        parameter_name=parameter_name,
        unit=unit,
        observed_at=when,
        value=value,
        qualifiers=("A",),
        provisional=False,
        estimated_tds_mg_l=None,
    )


def _write_history(path: Path, records: list[history.HistoricalObservation]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        for record in records:
            handle.write(json.dumps(asdict(record), sort_keys=True, separators=(",", ":")) + "\n")


def test_rebuild_csv_uses_bounded_external_sort_and_preserves_global_order(tmp_path: Path) -> None:
    jsonl = tmp_path / "normalized" / "history.jsonl"
    csv_path = tmp_path / "normalized" / "history.csv"
    records = [
        _record("B", "00065", "2024-01-03T00:00:00Z", 3.0),
        _record("A", "00060", "2024-01-01T00:00:00Z", 1.0),
        _record("A", "00065", "2024-01-02T00:00:00Z", 2.0),
    ]
    _write_history(jsonl, records)

    assert history.rebuild_csv(jsonl, csv_path, sort_chunk_rows=1) == 3
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["observed_at"] for row in rows] == [
        "2024-01-01T00:00:00Z",
        "2024-01-02T00:00:00Z",
        "2024-01-03T00:00:00Z",
    ]
    assert all(row["qualifiers"] == "A" for row in rows)


def test_sqlite_identity_index_syncs_and_supports_restart_safe_append(tmp_path: Path) -> None:
    jsonl = tmp_path / "normalized" / "history.jsonl"
    index_path = tmp_path / "backfill" / "identity_index.sqlite"
    first = _record("A", "00060", "2024-01-01T00:00:00Z", 1.0)
    second = _record("A", "00060", "2024-01-01T00:15:00Z", 2.0)
    _write_history(jsonl, [first])

    connection = history.open_identity_index(index_path, jsonl)
    try:
        assert history.identity_index_count(connection) == 1
        assert history.append_deduplicated_indexed(jsonl, [first, second, second], connection) == 1
        assert history.identity_index_count(connection) == 2
    finally:
        connection.close()

    reopened = history.open_identity_index(index_path, jsonl)
    try:
        assert history.identity_index_count(reopened) == 2
    finally:
        reopened.close()
    assert len(jsonl.read_text(encoding="utf-8").splitlines()) == 2


def test_finalize_completed_archive_makes_zero_network_requests(tmp_path: Path, monkeypatch) -> None:
    output_root = tmp_path / "nrhis"
    jsonl = output_root / "normalized" / "usgs_historical_observations.jsonl"
    checkpoint = output_root / "backfill" / "checkpoint.json"
    _write_history(
        jsonl,
        [
            _record("B", "00065", "2024-01-02T00:00:00Z", 2.0),
            _record("A", "00060", "2024-01-01T00:00:00Z", 1.0),
        ],
    )
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "requested_start": "2024-01-01",
                "requested_end": "2024-01-02",
                "completed_through": "2024-01-02",
            }
        ),
        encoding="utf-8",
    )

    def no_network(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("finalize-only must not call USGS")

    monkeypatch.setattr(history, "fetch_json", no_network)
    receipt = history.finalize_completed_archive(
        output_root,
        start_date="2024-01-01",
        end_date="2024-01-02",
    )

    assert receipt["finalize_only"] is True
    assert receipt["usgs_requests_made"] == 0
    assert receipt["total_history_records"] == 2
    assert receipt["identity_index_final_size"] == 2
    assert Path(receipt["history_csv"]).is_file()
    assert Path(receipt["identity_index"]).is_file()
    assert Path(receipt["receipt"]).is_file()


def test_finalize_rejects_incomplete_checkpoint(tmp_path: Path) -> None:
    output_root = tmp_path / "nrhis"
    jsonl = output_root / "normalized" / "usgs_historical_observations.jsonl"
    checkpoint = output_root / "backfill" / "checkpoint.json"
    _write_history(jsonl, [_record("A", "00060", "2024-01-01T00:00:00Z", 1.0)])
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.write_text(
        json.dumps(
            {
                "requested_start": "2024-01-01",
                "requested_end": "2024-01-02",
                "completed_through": "2024-01-01",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(history.BackfillError, match="does not show the requested archive range as complete"):
        history.finalize_completed_archive(
            output_root,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )


def test_finalize_wrapper_is_explicitly_network_free() -> None:
    script = Path("scripts/Finalize-USGS-History.ps1").read_text(encoding="utf-8")
    assert "finalize_usgs_history.py" in script
    assert "zero USGS requests" in script
