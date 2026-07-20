from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

from nrhis_harvest.usgs_incremental_update import (
    build_quality_summary,
    choose_incremental_start,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_incremental_start_uses_overlap(tmp_path: Path) -> None:
    history = tmp_path / "history.jsonl"
    _write_jsonl(
        history,
        [{"site_no": "1", "parameter_code": "00060", "observed_at": "2026-07-18T12:00:00Z"}],
    )
    result = choose_incremental_start(
        history,
        study_start=date(2024, 2, 1),
        end_date=date(2026, 7, 19),
        overlap_days=2,
    )
    assert result == date(2026, 7, 16)


def test_incremental_start_defaults_to_study_start(tmp_path: Path) -> None:
    result = choose_incremental_start(
        tmp_path / "missing.jsonl",
        study_start=date(2024, 2, 1),
        end_date=date(2026, 7, 19),
        overlap_days=2,
    )
    assert result == date(2024, 2, 1)


def test_quality_summary_flags_missing_and_gaps(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "stale_minutes": 90,
                "parameter_codes": ["00060"],
                "stations": [
                    {"site_no": "A", "name": "Station A"},
                    {"site_no": "B", "name": "Station B"},
                ],
            }
        ),
        encoding="utf-8",
    )
    history = tmp_path / "historical" / "usgs_observations_history.jsonl"
    _write_jsonl(
        history,
        [
            {"site_no": "A", "parameter_code": "00060", "observed_at": "2026-07-19T08:00:00Z"},
            {"site_no": "A", "parameter_code": "00060", "observed_at": "2026-07-19T12:30:00Z"},
        ],
    )
    result = build_quality_summary(
        config,
        history,
        tmp_path,
        assessed_at=datetime(2026, 7, 19, 13, 0, tzinfo=timezone.utc),
        lookback_days=1,
        gap_minutes=120,
        stale_minutes=90,
    )
    assert result["missing_station_parameters"] == 1
    assert result["detected_gaps"] == 1
    assert result["ready_for_reporting"] is False
    assert (tmp_path / "quality" / "usgs_data_quality_summary.json").exists()
    assert (tmp_path / "quality" / "usgs_detected_gaps.csv").exists()
