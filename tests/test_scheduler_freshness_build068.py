from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("scheduler_health_build068", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def base_config() -> dict:
    return {
        "tasks": [
            {"task_name": "NRHIS Operations - Morning", "hour": 7, "minute": 0},
            {"task_name": "NRHIS Operations - Evening", "hour": 18, "minute": 0},
        ],
        "expected_slots": [
            {"name": "Morning", "hour": 7, "minute": 0},
            {"name": "Evening", "hour": 18, "minute": 0},
        ],
        "grace_minutes": 90,
        "receipt_max_age_hours": 14,
        "operations_cycle_latest": "data/latest_cycle.json",
        "scheduler_receipt": "data/latest_scheduler_run.json",
    }


def test_recent_receipt_is_healthy(tmp_path: Path) -> None:
    module = load_module(Path("scripts/test_nrhis_scheduler_health.py"))
    write_json(tmp_path / "data/latest_cycle.json", {"status": "completed"})
    write_json(
        tmp_path / "data/latest_scheduler_run.json",
        {"status": "completed", "exit_code": 0, "completed_at": "2026-07-20T18:10:00Z"},
    )
    result = module.evaluate(
        tmp_path,
        base_config(),
        now=datetime(2026, 7, 20, 18, 20, tzinfo=timezone.utc),
    )
    assert result["healthy"] is True
    assert result["problems"] == []


def test_stale_receipt_is_reported(tmp_path: Path) -> None:
    module = load_module(Path("scripts/test_nrhis_scheduler_health.py"))
    write_json(tmp_path / "data/latest_cycle.json", {"status": "completed"})
    write_json(
        tmp_path / "data/latest_scheduler_run.json",
        {"status": "completed", "exit_code": 0, "completed_at": "2026-07-19T18:00:00Z"},
    )
    result = module.evaluate(
        tmp_path,
        base_config(),
        now=datetime(2026, 7, 20, 18, 20, tzinfo=timezone.utc),
    )
    assert "stale_scheduler_run_receipt" in result["problems"]


def test_missed_evening_slot_is_reported(tmp_path: Path) -> None:
    module = load_module(Path("scripts/test_nrhis_scheduler_health.py"))
    write_json(tmp_path / "data/latest_cycle.json", {"status": "completed"})
    write_json(
        tmp_path / "data/latest_scheduler_run.json",
        {"status": "completed", "exit_code": 0, "completed_at": "2026-07-20T07:10:00Z"},
    )
    result = module.evaluate(
        tmp_path,
        base_config(),
        now=datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc),
    )
    assert "missed_schedule_slot:Evening" in result["problems"]


def test_config_preserves_build066_contract() -> None:
    config = json.loads(Path("config/nrhis/scheduler_health.json").read_text(encoding="utf-8-sig"))
    assert config["build"] == "066"
    assert [slot["name"] for slot in config["expected_slots"]] == ["Morning", "Evening"]
