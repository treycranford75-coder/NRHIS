from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import nrhis_harvest.coastal_salt03_harvest as module
from nrhis_harvest.coastal_salt03_harvest import (
    CoastalHarvestError,
    append_deduplicated_jsonl,
    harvest,
    normalize_parameters,
    normalize_timeseries,
)


def test_normalize_parameters_and_timeseries() -> None:
    parameters = normalize_parameters([
        {"code": "seawater_salinity", "name": "Salinity", "units_abbreviation": "PSU"}
    ])
    assert parameters["seawater_salinity"]["units"] == "PSU"
    rows = normalize_timeseries(
        [{"value": 18.5, "datetime_utc": "2026-07-20T01:00:00Z"}],
        station_code="SALT03",
        station_name="SALT03 Nueces Bay",
        parameter_code="seawater_salinity",
        parameter_name="Salinity",
        units="PSU",
        retrieved_at=datetime(2026, 7, 20, 2, tzinfo=timezone.utc),
        stale_hours=6,
    )
    assert rows[0].value == 18.5
    assert rows[0].stale is False


def test_deduplicated_history(tmp_path: Path) -> None:
    rows = normalize_timeseries(
        [{"value": 18.5, "datetime_utc": "2026-07-20T01:00:00Z"}],
        station_code="SALT03", station_name="SALT03 Nueces Bay",
        parameter_code="seawater_salinity", parameter_name="Salinity", units="PSU",
        retrieved_at=datetime(2026, 7, 20, 2, tzinfo=timezone.utc), stale_hours=6,
    )
    path = tmp_path / "history.jsonl"
    assert append_deduplicated_jsonl(path, rows) == 1
    assert append_deduplicated_jsonl(path, rows) == 0


def test_harvest_writes_current_status_and_receipt(tmp_path: Path, monkeypatch) -> None:
    fixture = json.loads((Path(__file__).parent / "fixtures" / "salt03_build059.json").read_text())
    config = tmp_path / "config.json"
    config.write_text(json.dumps({
        "api_base": "https://example.test/coastal/api",
        "station_code": "SALT03",
        "station_name": "SALT03 Nueces Bay",
        "preferred_parameters": ["seawater_salinity", "water_temperature"],
        "required_parameters": ["seawater_salinity"],
        "lookback_hours": 24, "stale_hours": 6, "binning": "hour"
    }))

    def fake_fetch(url: str, timeout: int):
        if url.endswith("/parameters"):
            payload = fixture["parameters"]
        elif "seawater_salinity" in url:
            payload = fixture["salinity"]
        elif "water_temperature" in url:
            payload = fixture["temperature"]
        else:
            raise CoastalHarvestError("unexpected URL")
        raw = json.dumps(payload).encode()
        return payload, raw

    monkeypatch.setattr(module, "_fetch_json", fake_fetch)
    receipt = harvest(config, tmp_path / "data", retrieved_at=datetime(2026, 7, 20, 2, tzinfo=timezone.utc))
    assert receipt["observation_count"] == 3
    assert receipt["ready_for_reporting"] is True
    assert Path(receipt["files"]["current_json"]).exists()
    assert Path(receipt["files"]["parameter_status_csv"]).exists()
    assert Path(receipt["receipt_path"]).exists()
