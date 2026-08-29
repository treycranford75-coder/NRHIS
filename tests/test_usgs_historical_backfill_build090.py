from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from nrhis_harvest import usgs_historical_backfill as backfill


def _write_config(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "stations": [{"site_no": "08211200", "name": "Bluntzer"}],
                "parameter_codes": ["00060"],
            }
        ),
        encoding="utf-8",
    )


def test_resume_uses_checkpoint_when_scope_matches() -> None:
    checkpoint = {
        "requested_start": "2007-01-01",
        "completed_through": "2007-01-07",
    }
    start, used, reason = backfill.resolve_resume_start(checkpoint, date(2007, 1, 1))
    assert start == date(2007, 1, 8)
    assert used is True
    assert reason is None


def test_resume_ignores_newer_checkpoint_for_deeper_history() -> None:
    checkpoint = {
        "requested_start": "2024-02-01",
        "completed_through": "2026-08-29",
    }
    start, used, reason = backfill.resolve_resume_start(checkpoint, date(2007, 1, 1))
    assert start == date(2007, 1, 1)
    assert used is False
    assert reason == "checkpoint_requested_start_mismatch"


def test_backfill_does_not_skip_deeper_history(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    _write_config(config_path)
    output_root = tmp_path / "data"
    checkpoint_path = output_root / "backfill" / "checkpoint.json"
    checkpoint_path.parent.mkdir(parents=True)
    checkpoint_path.write_text(
        json.dumps(
            {
                "requested_start": "2024-02-01",
                "requested_end": "2026-08-29",
                "completed_through": "2026-08-29",
            }
        ),
        encoding="utf-8",
    )

    requested_urls: list[str] = []

    def fake_fetch(url: str, timeout_seconds: int = 60) -> bytes:
        del timeout_seconds
        requested_urls.append(url)
        return b'{"value":{"timeSeries":[]}}'

    monkeypatch.setattr(backfill, "fetch_json", fake_fetch)
    receipt = backfill.backfill(
        config_path,
        output_root,
        start_date="2007-01-01",
        end_date="2007-01-02",
        chunk_days=7,
        resume=True,
    )

    assert len(requested_urls) == 1
    assert "startDT=2007-01-01" in requested_urls[0]
    assert "endDT=2007-01-02" in requested_urls[0]
    assert receipt["effective_start"] == "2007-01-01"
    assert receipt["checkpoint_used"] is False
    assert receipt["checkpoint_ignored_reason"] == "checkpoint_requested_start_mismatch"
