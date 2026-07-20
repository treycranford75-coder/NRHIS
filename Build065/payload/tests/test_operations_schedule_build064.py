from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_schedule_config_has_twice_daily_slots() -> None:
    config = json.loads((ROOT / "config/nrhis/operations_schedule.json").read_text(encoding="utf-8"))
    assert int(config["build"]) >= 64
    assert config["morning"]["time"] == "07:00"
    assert config["evening"]["time"] == "18:00"
    assert config["qa_passes_completed"] == 0


def test_scheduler_scripts_are_noninteractive_and_auditable() -> None:
    install = (ROOT / "scripts/Install-NrhisOperationsSchedule.ps1").read_text(encoding="utf-8")
    runner = (ROOT / "scripts/Run-NrhisScheduledCycle.ps1").read_text(encoding="utf-8")
    assert "Register-ScheduledTask" in install
    assert "-ExecutionPolicy\", \"Bypass" in install
    assert "Tee-Object -FilePath" in runner
    assert "latest-{0}.json" in runner


def test_schedule_can_be_removed_and_inspected() -> None:
    remove = (ROOT / "scripts/Remove-NrhisOperationsSchedule.ps1").read_text(encoding="utf-8")
    status = (ROOT / "scripts/Get-NrhisOperationsScheduleStatus.ps1").read_text(encoding="utf-8")
    assert "Unregister-ScheduledTask" in remove
    assert "Get-ScheduledTaskInfo" in status
