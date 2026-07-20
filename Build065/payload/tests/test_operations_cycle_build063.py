from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from nrhis_harvest.operations_cycle import _default_runner, build_steps, run_cycle


def _config(path: Path, *, timeout: int = 300) -> Path:
    cfg = {
        "scripts_directory": "scripts",
        "evidence_directory": "data/nrhis/operations_cycles",
        "powershell_executable": "powershell.exe",
        "stop_on_required_failure": True,
        "step_timeout_seconds": timeout,
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


def test_cycle_runs_noninteractive_in_order_and_writes_receipt(tmp_path: Path) -> None:
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
    assert receipt["build"] == "063"
    assert receipt["step_timeout_seconds"] == 300
    assert len(commands) == 10
    assert all("-NonInteractive" in command for command in commands)
    assert commands[-1][-2:] == ["-QaPassesCompleted", "2"]
    assert Path(receipt["receipt_path"]).exists()


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


def test_missing_required_script_is_recorded(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "repo")
    (repo / "scripts" / "Harvest-USGS-Production.ps1").unlink()
    config = _config(tmp_path / "config.json")
    fixed = datetime(2026, 7, 20, 7, 0, tzinfo=timezone.utc)
    receipt = run_cycle(config, repo, now=lambda: fixed)
    assert receipt["status"] == "failed"
    assert receipt["steps"][0]["exit_code"] == 127


def test_default_runner_converts_timeout_to_exit_124(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=["pwsh"], timeout=7, output="partial", stderr="late")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = _default_runner(["pwsh"], Path("."), timeout_seconds=7)
    assert result.returncode == 124
    assert "partial" in result.stdout
    assert "timed out after 7 seconds" in result.stderr


def test_wrapper_contracts_use_safe_runtime_paths_and_recent_incremental_window() -> None:
    root = Path(__file__).resolve().parents[1]
    current = (root / "scripts" / "Harvest-USGS-Production.ps1").read_text(encoding="utf-8")
    incremental = (root / "scripts" / "Update-USGS-Incremental.ps1").read_text(encoding="utf-8")
    assert "[string]$RepositoryRoot," in current
    assert "[string]$OutputRoot," in current
    assert "$MaxAttempts = 3" in current
    assert "Start-Sleep" in current
    assert 'AddDays(-2)' in incremental
    assert "[string]$RepositoryRoot," in incremental
