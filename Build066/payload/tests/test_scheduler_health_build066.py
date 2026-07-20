from __future__ import annotations

import json
from pathlib import Path


def test_build066_config_has_two_slots() -> None:
    path = Path("config/nrhis/scheduler_health.json")
    if not path.exists():
        path = Path("payload/config/nrhis/scheduler_health.json")
    config = json.loads(path.read_text(encoding="utf-8"))
    assert [slot["name"] for slot in config["expected_slots"]] == ["Morning", "Evening"]
    assert config["build"] == "066"


def test_build066_wrapper_supports_fail_on_unhealthy() -> None:
    path = Path("scripts/Test-NrhisSchedulerHealth.ps1")
    if not path.exists():
        path = Path("payload/scripts/Test-NrhisSchedulerHealth.ps1")
    text = path.read_text(encoding="utf-8")
    assert "FailOnUnhealthy" in text
    assert "--fail-on-unhealthy" in text
