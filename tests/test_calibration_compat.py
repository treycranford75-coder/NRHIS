"""Tests for the additive legacy Pass1 compatibility wrapper."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from nrhis_calibration import (
    LegacyPass1Error,
    build_legacy_pass1_command,
    run_legacy_pass1,
)
from nrhis_calibration import compat

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LEGACY_ROOT = REPOSITORY_ROOT / "src" / "nrhis_calibration" / "legacy"
LEGACY_SCRIPT = LEGACY_ROOT / "calibrate_pass1.py"


def test_build_command_targets_preserved_script() -> None:
    command = build_legacy_pass1_command(
        python_executable=sys.executable,
        extra_args=("--example", "value"),
    )
    assert command[0] == sys.executable
    assert Path(command[1]) == LEGACY_SCRIPT
    assert command[2:] == ("--example", "value")


def test_dry_run_creates_structured_artifacts(tmp_path: Path) -> None:
    result = run_legacy_pass1(output_root=tmp_path, dry_run=True)
    assert result.succeeded
    metadata = json.loads(Path(result.metadata_path).read_text(encoding="utf-8"))
    assert metadata["dry_run"] is True
    assert metadata["succeeded"] is True
    assert metadata["command"][1] == str(LEGACY_SCRIPT)


def test_subprocess_success_is_captured(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class Completed:
        stdout = "ok\n"
        stderr = ""
        returncode = 0

    def fake_run(*args: object, **kwargs: object) -> Completed:
        assert kwargs["cwd"] == LEGACY_ROOT
        return Completed()

    monkeypatch.setattr(compat.subprocess, "run", fake_run)
    result = run_legacy_pass1(output_root=tmp_path)
    assert result.succeeded
    assert Path(result.stdout_path).read_text(encoding="utf-8") == "ok\n"


def test_timeout_is_recorded_as_exit_code_124(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_run(*args: object, **kwargs: object) -> object:
        raise compat.subprocess.TimeoutExpired(
            cmd=kwargs.get("args", args[0] if args else "legacy"),
            timeout=1,
            output="partial output",
            stderr="timed out",
        )

    monkeypatch.setattr(compat.subprocess, "run", fake_run)
    result = run_legacy_pass1(output_root=tmp_path, timeout_seconds=1)
    assert not result.succeeded
    assert result.return_code == 124


def test_missing_legacy_script_raises_controlled_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(compat, "LEGACY_SCRIPT", LEGACY_ROOT / "missing.py")
    with pytest.raises(LegacyPass1Error, match="script is missing"):
        build_legacy_pass1_command()
