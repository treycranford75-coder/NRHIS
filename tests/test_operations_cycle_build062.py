from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from nrhis_harvest.operations_cycle import build_steps, run_cycle


def _config(path: Path) -> Path:
    cfg = {
        "scripts_directory": "scripts",
        "evidence_directory": "data/nrhis/operations_cycles",
        "powershell_executable": "powershell.exe",
        "stop_on_required_failure": True,
        "disabled_steps": [],
        "required_steps": {},
    }
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _repo(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".git").mkdir()
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for step in build_steps({}, qa_passes_completed=0):
        (scripts / step.script).write_text("# test\n", encoding="utf-8")
    return tmp_path


def test_publication_step_receives_qa_count() -> None:
    steps = build_steps({}, qa_passes_completed=2)
    publication = next(step for step in steps if step.name == "publication_bundle")
    assert publication.arguments == ("-QaPassesCompleted", "2")


def test_cycle_runs_in_order_and_writes_receipt(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "repo")
    config = _config(tmp_path / "config.json")
    commands: list[list[str]] = []

    def runner(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    fixed = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)
    receipt = run_cycle(
        config,
        repo,
        qa_passes_completed=2,
        cycle_name="morning-test",
        runner=runner,
        now=lambda: fixed,
    )
    assert receipt["status"] == "completed"
    assert receipt["publication_authorized"] is True
    assert len(commands) == 10
    assert commands[-1][-2:] == ["-QaPassesCompleted", "2"]
    assert Path(receipt["receipt_path"]).exists()
    assert Path(receipt["latest_path"]).exists()


def test_required_failure_stops_cycle(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "repo")
    config = _config(tmp_path / "config.json")
    calls = 0

    def runner(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        nonlocal calls
        calls += 1
        code = 1 if calls == 2 else 0
        return subprocess.CompletedProcess(command, code, stdout="", stderr="failed\n")

    fixed = datetime(2026, 7, 20, 18, 0, tzinfo=timezone.utc)
    receipt = run_cycle(config, repo, runner=runner, now=lambda: fixed)
    assert receipt["status"] == "failed"
    assert receipt["blocked"] is True
    assert calls == 2
    assert receipt["required_failures"] == ["usgs_incremental"]
    assert receipt["publication_authorized"] is False


def test_missing_required_script_is_recorded(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "repo")
    (repo / "scripts" / "Harvest-USGS-Production.ps1").unlink()
    config = _config(tmp_path / "config.json")
    fixed = datetime(2026, 7, 20, 7, 0, tzinfo=timezone.utc)
    receipt = run_cycle(config, repo, now=lambda: fixed)
    assert receipt["status"] == "failed"
    assert receipt["steps"][0]["exit_code"] == 127
    assert Path(receipt["steps"][0]["log_path"]).exists()
