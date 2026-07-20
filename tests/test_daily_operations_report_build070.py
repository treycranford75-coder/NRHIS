from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def load_module():
    path = Path("scripts/build_daily_operations_report.py")
    spec = importlib.util.spec_from_file_location("daily_report_build070", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def seed(root: Path, qa_authorized: bool = True) -> Path:
    config = {
        "report_title": "Test Report",
        "required_qa_passes": 2,
        "inputs": {
            "operations_cycle": "in/cycle.json",
            "integrated_snapshot": "in/snapshot.json",
            "usgs_current": "in/usgs.json",
            "reservoir_summary": "in/reservoirs.json",
            "reservoir_water_budget": "in/budget.json",
            "reservoir_response": "in/response.json",
            "salt03": "in/salt03.json",
            "scheduler_health": "in/health.json",
            "scheduler_alert": "in/alert.json",
        },
        "outputs": {
            "json": "out/report.json",
            "markdown": "out/report.md",
            "html": "out/report.html",
            "history_jsonl": "out/history.jsonl",
            "receipt": "out/receipt.json",
        },
        "stations": [{"site_no": "08210000", "label": "Three Rivers"}],
        "reservoirs": [{"id": "choke_canyon", "label": "Choke Canyon Reservoir"}],
    }
    (root / "config.json").write_text(json.dumps(config), encoding="utf-8")
    (root / "in").mkdir()
    values = {
        "cycle.json": {"status": "completed", "publication_authorized": qa_authorized},
        "snapshot.json": {},
        "usgs.json": {"stations": [{"site_no": "08210000", "discharge_cfs": 123.4}]},
        "reservoirs.json": {"reservoirs": [{"reservoir_id": "choke_canyon", "storage_acft": 1000}]},
        "budget.json": {"reservoirs": [{"reservoir_id": "choke_canyon", "evaporation_mgd": 2.2}]},
        "response.json": {"reservoirs": [{"reservoir_id": "choke_canyon", "confidence": "moderate"}]},
        "salt03.json": {"salinity_psu": 8.1},
        "health.json": {"status": "healthy"},
        "alert.json": {"severity": "info"},
    }
    for name, value in values.items():
        (root / "in" / name).write_text(json.dumps(value), encoding="utf-8")
    return root / "config.json"


def test_authorized_report_outputs_all_formats(tmp_path: Path):
    module = load_module()
    config = seed(tmp_path)
    report = module.build(tmp_path, config, 2)
    assert report["publication_status"] == "authorized"
    assert report["stations"][0]["discharge_cfs"] == 123.4
    assert (tmp_path / "out/report.json").exists()
    assert (tmp_path / "out/report.md").exists()
    assert (tmp_path / "out/report.html").exists()
    assert (tmp_path / "out/receipt.json").exists()


def test_report_is_held_before_two_qa_passes(tmp_path: Path):
    module = load_module()
    config = seed(tmp_path)
    report = module.build(tmp_path, config, 1)
    assert report["publication_status"] == "pending_qa"
    assert any("Two-pass QA" in reason for reason in report["release_hold_reasons"])


def test_missing_required_source_holds_publication(tmp_path: Path):
    module = load_module()
    config = seed(tmp_path)
    (tmp_path / "in/usgs.json").unlink()
    report = module.build(tmp_path, config, 2)
    assert report["publication_status"] == "pending_qa"
    assert "usgs_current" in report["missing_inputs"]


def test_history_is_append_only(tmp_path: Path):
    module = load_module()
    config = seed(tmp_path)
    module.build(tmp_path, config, 2)
    module.build(tmp_path, config, 2)
    lines = (tmp_path / "out/history.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
