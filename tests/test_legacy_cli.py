"""Tests for the legacy Pass1 command-line adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from nrhis_calibration import legacy_cli


class FakeResult:
    run_id = "20260718T120000Z"
    return_code = 0
    metadata_path = "metadata.json"
    stdout_path = "stdout.log"
    stderr_path = "stderr.log"


def test_cli_dry_run_invokes_wrapper(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    def fake_run_legacy_pass1(**kwargs: object) -> FakeResult:
        captured.update(kwargs)
        return FakeResult()

    monkeypatch.setattr(legacy_cli, "run_legacy_pass1", fake_run_legacy_pass1)
    monkeypatch.setattr(
        "sys.argv",
        [
            "legacy_cli",
            "--output-root",
            str(tmp_path),
            "--dry-run",
            "--timeout-seconds",
            "30",
            "--extra-arg=--sample",
        ],
    )

    assert legacy_cli.main() == 0
    assert captured["output_root"] == str(tmp_path)
    assert captured["dry_run"] is True
    assert captured["timeout_seconds"] == 30.0
    assert captured["extra_args"] == ("--sample",)

    output = capsys.readouterr().out
    assert "Return code: 0" in output


def test_cli_propagates_nonzero_return_code(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class FailedResult(FakeResult):
        return_code = 7

    monkeypatch.setattr(
        legacy_cli,
        "run_legacy_pass1",
        lambda **kwargs: FailedResult(),
    )
    monkeypatch.setattr(
        "sys.argv",
        ["legacy_cli", "--output-root", str(tmp_path)],
    )

    assert legacy_cli.main() == 7
