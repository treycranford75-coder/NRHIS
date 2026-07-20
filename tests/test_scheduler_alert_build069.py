from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def load_module():
    path = Path("scripts/build_scheduler_alert.py")
    if not path.exists():
        path = Path("payload/scripts/build_scheduler_alert.py")
    spec = importlib.util.spec_from_file_location("scheduler_alert_build069", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_alert_clear() -> None:
    module = load_module()
    result = module.build_alert(
        {
            "build": "068",
            "checked_at": "2026-07-20T12:00:00Z",
            "healthy": True,
            "problems": [],
            "tasks": [],
        }
    )
    assert result["status"] == "clear"
    assert result["severity"] == "info"
    assert result["healthy"] is True


def test_build_alert_warning_for_stale_receipt() -> None:
    module = load_module()
    result = module.build_alert(
        {
            "healthy": False,
            "problems": ["stale_scheduler_run_receipt"],
            "tasks": [],
        }
    )
    assert result["status"] == "active"
    assert result["severity"] == "warning"


def test_build_alert_critical_for_missed_slot() -> None:
    module = load_module()
    result = module.build_alert(
        {
            "healthy": False,
            "problems": ["missed_schedule_slot:Morning"],
            "tasks": [],
        }
    )
    assert result["severity"] == "critical"


def test_run_writes_alert_receipt_and_deduplicated_history(tmp_path: Path) -> None:
    module = load_module()
    health_path = tmp_path / "data/nrhis/scheduler/scheduler_health.json"
    health_path.parent.mkdir(parents=True)
    health_path.write_text(
        json.dumps(
            {
                "build": "068",
                "checked_at": "2026-07-20T12:00:00Z",
                "healthy": False,
                "problems": ["missed_schedule_slot:Evening"],
                "tasks": [],
                "files": {},
            }
        ),
        encoding="utf-8",
    )
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "scheduler_health_json": "data/nrhis/scheduler/scheduler_health.json",
                "output_json": "data/nrhis/scheduler/scheduler_alert.json",
                "output_markdown": "data/nrhis/scheduler/scheduler_alert.md",
                "history_jsonl": "data/nrhis/scheduler/scheduler_alert_history.jsonl",
                "output_receipt": "data/nrhis/receipts/scheduler_alert_receipt.json",
            }
        ),
        encoding="utf-8",
    )
    first = module.run(tmp_path, config_path)
    second = module.run(tmp_path, config_path)
    assert first["severity"] == "critical"
    assert second["status"] == "active"
    history = tmp_path / "data/nrhis/scheduler/scheduler_alert_history.jsonl"
    assert len(history.read_text(encoding="utf-8").splitlines()) == 1
    assert (tmp_path / "data/nrhis/receipts/scheduler_alert_receipt.json").exists()
