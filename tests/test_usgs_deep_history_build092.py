from __future__ import annotations

import hashlib
import json
from pathlib import Path

from nrhis_harvest import usgs_historical_backfill as history


def _record(site: str, when: str, value: float = 1.0) -> history.HistoricalObservation:
    return history.HistoricalObservation(
        site_no=site,
        site_name=f"Site {site}",
        parameter_code="00060",
        parameter_name="discharge",
        unit="ft3/s",
        observed_at=when,
        value=value,
        qualifiers=("A",),
        provisional=False,
        estimated_tds_mg_l=None,
    )


def test_append_reuses_supplied_identity_index(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "history.jsonl"
    known = {"A|00060|2020-01-01T00:00:00Z"}

    def should_not_be_called(_: Path) -> set[str]:
        raise AssertionError("existing_identities should not be rescanned when a set is supplied")

    monkeypatch.setattr(history, "existing_identities", should_not_be_called)
    records = [
        _record("A", "2020-01-01T00:00:00Z"),
        _record("A", "2020-01-01T00:15:00Z"),
        _record("A", "2020-01-01T00:15:00Z"),
    ]
    assert history.append_deduplicated(path, records, known) == 1
    assert "A|00060|2020-01-01T00:15:00Z" in known
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1


def test_raw_evidence_bytes_match_recorded_hash_and_conflicts_are_preserved(tmp_path: Path) -> None:
    path = tmp_path / "raw" / "chunk.json"
    raw_a = b'{"source":"USGS","value":1}\n'
    raw_b = b'{"source":"USGS","value":2}\n'

    first = history.write_raw_evidence(path, raw_a)
    repeated = history.write_raw_evidence(path, raw_a)
    second = history.write_raw_evidence(path, raw_b)

    assert first == path
    assert repeated == path
    assert first.read_bytes() == raw_a
    assert hashlib.sha256(first.read_bytes()).hexdigest() == hashlib.sha256(raw_a).hexdigest()
    assert second != first
    assert second.read_bytes() == raw_b
    assert second.name.endswith(".json")
    assert hashlib.sha256(second.read_bytes()).hexdigest() == hashlib.sha256(raw_b).hexdigest()


def test_rincon_stations_are_in_historical_registry() -> None:
    config_path = Path("config/nrhis/usgs_nueces_basin.json")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    site_numbers = {station["site_no"] for station in config["stations"]}
    assert "08211503" in site_numbers
    assert "0821150305" in site_numbers


def test_plan_only_exposes_station_registry() -> None:
    script = Path("scripts/Bootstrap-USGS-History.ps1").read_text(encoding="utf-8")
    assert "Configured stations:" in script
    assert "parameter_codes" in script
    assert "USGS returns only series that actually exist" in script
