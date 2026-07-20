import json
from pathlib import Path
import importlib.util


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("scheduler_health_build067", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_config_uses_canonical_scheduler_receipt():
    cfg = json.loads(Path("config/nrhis/scheduler_health.json").read_text(encoding="utf-8-sig"))
    assert cfg["scheduler_receipt"] == "data/nrhis/scheduler/latest_scheduler_run.json"


def test_health_accepts_valid_receipt(tmp_path):
    mod = load_module(Path("scripts/test_nrhis_scheduler_health.py"))
    (tmp_path / "data/nrhis/operations_cycles").mkdir(parents=True)
    (tmp_path / "data/nrhis/scheduler").mkdir(parents=True)
    (tmp_path / "data/nrhis/operations_cycles/latest_operations_cycle.json").write_text(
        '{"status":"completed"}', encoding="utf-8"
    )
    (tmp_path / "data/nrhis/scheduler/latest_scheduler_run.json").write_text(
        '{"status":"completed","exit_code":0}', encoding="utf-8"
    )
    cfg = {
        "tasks": [],
        "operations_cycle_latest": "data/nrhis/operations_cycles/latest_operations_cycle.json",
        "scheduler_receipt": "data/nrhis/scheduler/latest_scheduler_run.json",
    }
    result = mod.evaluate(tmp_path, cfg)
    assert result["healthy"] is True
    assert result["problems"] == []


def test_loader_accepts_utf8_bom(tmp_path):
    mod = load_module(Path("scripts/test_nrhis_scheduler_health.py"))
    p = tmp_path / "receipt.json"
    p.write_bytes(b'\xef\xbb\xbf{"status":"completed","exit_code":0}')
    assert mod._load_optional(p)["status"] == "completed"
