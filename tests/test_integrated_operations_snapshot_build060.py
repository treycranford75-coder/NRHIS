from __future__ import annotations

import json
from pathlib import Path

from nrhis_harvest.integrated_operations_snapshot import build_integrated_rows, run


def test_build_integrated_rows_adds_river_and_coastal_records() -> None:
    rows = build_integrated_rows(
        [{"site_no": "08211500", "station_name": "Calallen", "discharge_cfs": 20, "stale": False}],
        [{"site_no": "08211500", "forecast_category": "below_flood", "forecast_peak_flow_cfs": 50}],
        [
            {"parameter_code": "salinity", "parameter_name": "Salinity", "value": 18.2, "stale": False},
            {"parameter_code": "do", "parameter_name": "Dissolved oxygen", "value": 6.5, "stale": False},
        ],
        {"coastal_station_code": "SALT03", "coastal_station_name": "SALT03 Nueces Bay"},
    )
    assert len(rows) == 2
    assert rows[0].status == "ready"
    assert rows[0].forecast_peak_value == 50
    assert rows[1].station_id == "SALT03"
    assert rows[1].salinity_psu == 18.2
    assert rows[1].status == "ready"


def test_missing_required_observations_hold_public_graphic() -> None:
    rows = build_integrated_rows(
        [{"site_no": "08211500", "station_name": "Calallen", "stale": True}],
        [],
        [],
        {},
    )
    assert rows[0].status == "not_ready"
    assert rows[1].status == "not_ready"


def test_run_writes_release_gate_outputs(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text("{}", encoding="utf-8")
    data = tmp_path / "data"
    (data / "operational").mkdir(parents=True)
    (data / "nwps").mkdir(parents=True)
    (data / "coastal").mkdir(parents=True)
    (data / "reservoirs").mkdir(parents=True)
    (data / "operational" / "basin_operational_snapshot.json").write_text(
        json.dumps([{"site_no": "08211500", "discharge_cfs": 10, "stale": False}]), encoding="utf-8"
    )
    (data / "nwps" / "nwps_forecasts.json").write_text("[]", encoding="utf-8")
    (data / "coastal" / "salt03_current_conditions.json").write_text(
        json.dumps([{"parameter_code": "salinity", "parameter_name": "Salinity", "value": 15, "stale": False}]),
        encoding="utf-8",
    )
    (data / "reservoirs" / "reservoir_operations_summary.json").write_text("[]", encoding="utf-8")
    receipt = run(config, data)
    assert receipt["overall_status"] == "ready"
    readiness = json.loads((data / "operational" / "integrated_reporting_readiness.json").read_text(encoding="utf-8"))
    assert readiness["public_graphic_allowed"] is True
