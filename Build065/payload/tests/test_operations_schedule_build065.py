from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_schedule_config_advances_to_build065() -> None:
    config = json.loads((ROOT / "config/nrhis/operations_schedule.json").read_text(encoding="utf-8"))
    assert config["build"] == "065"
    assert config["morning"]["time"] == "07:00"
    assert config["evening"]["time"] == "18:00"
    assert config["qa_passes_completed"] == 0


def test_installer_requires_elevation_and_fails_closed() -> None:
    install = (ROOT / "scripts/Install-NrhisOperationsSchedule.ps1").read_text(encoding="utf-8")
    assert "Test-IsAdministrator" in install
    assert "Administrator privileges are required" in install
    assert "Register-ScheduledTask" in install
    assert "-ErrorAction Stop" in install
    assert "Installed and verified" in install
    assert "Schedule verification failed" in install


def test_scheduled_action_uses_process_scoped_bypass() -> None:
    install = (ROOT / "scripts/Install-NrhisOperationsSchedule.ps1").read_text(encoding="utf-8")
    assert '"-ExecutionPolicy", "Bypass"' in install
    assert '"-NoProfile"' in install
    assert "Get-ScheduledTask -TaskName $taskName -ErrorAction Stop" in install
