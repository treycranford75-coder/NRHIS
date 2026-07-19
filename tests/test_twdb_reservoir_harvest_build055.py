from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from nrhis_harvest.twdb_reservoir_harvest import append_deduplicated_jsonl, parse_geojson


def _config() -> dict:
    return {
        "stale_days": 3,
        "reservoirs": [
            {"condensed_name": "ChokeCanyon", "display_order": 10},
            {"condensed_name": "CorpusChristi", "display_order": 20},
        ],
    }


def _payload() -> dict:
    path = Path(__file__).parent / "fixtures" / "twdb_reservoirs_build055.geojson"
    return json.loads(path.read_text(encoding="utf-8"))


def test_parse_two_reservoirs_and_change() -> None:
    rows = parse_geojson(
        _payload(),
        _config(),
        now=datetime(2026, 7, 19, tzinfo=timezone.utc),
        prior_storage={"ChokeCanyon": 54000, "CorpusChristi": 87500},
    )
    assert [row.reservoir_id for row in rows] == ["ChokeCanyon", "CorpusChristi"]
    assert rows[0].storage_change_acft == 1000
    assert rows[1].storage_change_acft == 500
    assert not any(row.stale for row in rows)


def test_deduplicated_history(tmp_path: Path) -> None:
    rows = parse_geojson(_payload(), _config(), now=datetime(2026, 7, 19, tzinfo=timezone.utc))
    history = tmp_path / "history.jsonl"
    assert append_deduplicated_jsonl(history, rows) == 2
    assert append_deduplicated_jsonl(history, rows) == 0
