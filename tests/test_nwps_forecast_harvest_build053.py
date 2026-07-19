from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import nrhis_harvest.nwps_forecast_harvest as module
from nrhis_harvest.nwps_forecast_harvest import classify_peak, harvest, normalize_categories


def test_categories_and_peak_classification() -> None:
    thresholds = normalize_categories(
        {"categories": {"action": {"stage": 12}, "minor": {"stage": 15}, "moderate": {"stage": 18}, "major": {"stage": 22}}}
    )
    assert thresholds[1]["category"] == "minor"
    assert classify_peak(16.5, None, thresholds) == "minor"
    assert classify_peak(10.0, None, thresholds) == "not_defined"


def test_harvest_writes_forecasts_thresholds_and_receipt(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "api_base": "https://example.test/nwps/v1",
                "gauges": [{"identifier": "TEST1", "usgs_site_no": "00000001", "name": "Test Gauge"}],
                "source_policy": {"observations": "USGS", "forecast_and_thresholds": "NWPS"},
            }
        ),
        encoding="utf-8",
    )
    stageflow = json.loads((Path(__file__).parent / "fixtures" / "nwps_stageflow_build053.json").read_text(encoding="utf-8"))
    metadata = {"categories": {"action": {"stage": 12}, "minor": {"stage": 15}, "moderate": {"stage": 18}, "major": {"stage": 22}}}

    def fake_fetch(url: str, timeout_seconds: int):
        payload = stageflow if url.endswith("/stageflow") else metadata
        raw = json.dumps(payload).encode("utf-8")
        return payload, raw

    monkeypatch.setattr(module, "_fetch_json", fake_fetch)
    receipt = harvest(config, tmp_path / "out", retrieved_at=datetime(2026, 7, 19, 13, tzinfo=timezone.utc))
    assert receipt["summary"]["successful_gauges"] == 1
    assert receipt["summary"]["forecast_points"] == 3
    assert receipt["summary"]["ready_for_reporting"] is True
    readiness = json.loads((tmp_path / "out" / "nwps" / "nwps_readiness.json").read_text(encoding="utf-8"))
    assert readiness["stations"][0]["forecast_category"] == "minor"
    assert (tmp_path / "out" / "nwps" / "nwps_flood_thresholds.csv").exists()
    assert (tmp_path / "out" / "receipts" / "nwps_forecast_harvest_receipt.json").exists()


def test_station_failure_is_isolated(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"gauges": [{"identifier": "BAD", "name": "Bad Gauge"}]}), encoding="utf-8")

    def fail(url: str, timeout_seconds: int):
        raise module.NwpsHarvestError("offline")

    monkeypatch.setattr(module, "_fetch_json", fail)
    receipt = harvest(config, tmp_path / "out")
    assert receipt["summary"]["successful_gauges"] == 0
    assert receipt["summary"]["ready_for_reporting"] is False
