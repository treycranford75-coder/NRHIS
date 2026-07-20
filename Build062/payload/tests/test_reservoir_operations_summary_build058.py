from __future__ import annotations

import json
from pathlib import Path

from nrhis_harvest.reservoir_operations_summary import build_summary, run


CONFIG = {
    "reservoir_order": ["ChokeCanyon", "CorpusChristi"],
    "display_names": {
        "ChokeCanyon": "Choke Canyon Reservoir",
        "CorpusChristi": "Lake Corpus Christi",
    },
}


def test_build_summary_ready_and_conditional() -> None:
    current = [
        {
            "reservoir_id": "ChokeCanyon",
            "reservoir_name": "Choke Canyon Reservoir",
            "conservation_storage_acft": 200000,
            "conservation_capacity_acft": 695271,
            "percent_full": 28.8,
            "surface_area_acres": 14000,
            "stale": False,
        },
        {
            "reservoir_id": "CorpusChristi",
            "reservoir_name": "Lake Corpus Christi",
            "conservation_storage_acft": 150000,
            "conservation_capacity_acft": 256062,
            "percent_full": 58.6,
            "surface_area_acres": 12000,
            "stale": False,
        },
    ]
    budgets = [
        {
            "reservoir_id": "ChokeCanyon",
            "budget_complete": True,
            "evaporation_acft_per_day": 100,
            "evaporation_mgd": 32.585,
        },
        {
            "reservoir_id": "CorpusChristi",
            "budget_complete": False,
            "evaporation_acft_per_day": 80,
            "evaporation_mgd": 26.068,
        },
    ]
    responses = [
        {
            "reservoir_id": "ChokeCanyon",
            "confidence": "moderate",
            "estimated_event_gain_central_acft": 10000,
            "projected_storage_central_acft": 210000,
            "projected_percent_full_central": 30.2,
            "basis": "forecast basis",
            "caveat": "changes as new data arrive",
        },
        {
            "reservoir_id": "CorpusChristi",
            "confidence": "low",
            "basis": "no usable forecast",
            "caveat": "changes as new data arrive",
        },
    ]

    rows = build_summary(current, budgets, responses, CONFIG)
    assert rows[0].operations_status == "ready"
    assert rows[0].projected_storage_central_acft == 210000
    assert rows[1].operations_status == "conditional"
    assert "water budget incomplete" in rows[1].status_reasons
    assert "confidence is low" in rows[1].status_reasons


def test_missing_current_record_is_not_ready() -> None:
    rows = build_summary([], [], [], CONFIG)
    assert len(rows) == 2
    assert all(row.operations_status == "not_ready" for row in rows)


def test_run_writes_summary_readiness_and_receipt(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(CONFIG), encoding="utf-8")
    root = tmp_path / "data"
    reservoir_dir = root / "reservoirs"
    reservoir_dir.mkdir(parents=True)
    (reservoir_dir / "reservoir_current_conditions.json").write_text(
        json.dumps(
            [
                {
                    "reservoir_id": "ChokeCanyon",
                    "reservoir_name": "Choke Canyon Reservoir",
                    "conservation_storage_acft": 200000,
                    "conservation_capacity_acft": 695271,
                    "percent_full": 28.8,
                    "stale": False,
                },
                {
                    "reservoir_id": "CorpusChristi",
                    "reservoir_name": "Lake Corpus Christi",
                    "conservation_storage_acft": 150000,
                    "conservation_capacity_acft": 256062,
                    "percent_full": 58.6,
                    "stale": False,
                },
            ]
        ),
        encoding="utf-8",
    )
    (reservoir_dir / "reservoir_water_budget_current.json").write_text(
        json.dumps(
            [
                {"reservoir_id": "ChokeCanyon", "budget_complete": True},
                {"reservoir_id": "CorpusChristi", "budget_complete": True},
            ]
        ),
        encoding="utf-8",
    )
    (reservoir_dir / "reservoir_response_estimate.json").write_text(
        json.dumps(
            [
                {"reservoir_id": "ChokeCanyon", "confidence": "moderate"},
                {"reservoir_id": "CorpusChristi", "confidence": "moderate"},
            ]
        ),
        encoding="utf-8",
    )

    receipt = run(config_path, root)
    assert receipt["overall_status"] == "ready"
    assert Path(receipt["files"]["json"]).exists()
    assert Path(receipt["files"]["csv"]).exists()
    assert Path(receipt["files"]["readiness"]).exists()
    assert Path(receipt["receipt_path"]).exists()
