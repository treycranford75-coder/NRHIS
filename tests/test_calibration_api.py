from pathlib import Path

import pytest

from nrhis_calibration import (
    CalibrationRunRequest,
    LegacyPass1CalibrationRunner,
    get_calibration_runner,
    run_calibration,
)
from nrhis_calibration import api


class FakeLegacyResult:
    run_id = "20260718T150000Z"
    return_code = 0
    succeeded = True
    metadata_path = "metadata.json"
    stdout_path = "stdout.log"
    stderr_path = "stderr.log"


def test_registry_returns_legacy_runner() -> None:
    assert isinstance(get_calibration_runner("legacy-pass1"), LegacyPass1CalibrationRunner)


def test_registry_normalizes_name() -> None:
    assert get_calibration_runner("  LEGACY-PASS1  ").implementation_name == "legacy-pass1"


def test_registry_rejects_unknown_implementation() -> None:
    with pytest.raises(ValueError, match="Unknown calibration implementation"):
        get_calibration_runner("modern-pass2")


def test_public_run_maps_legacy_result(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}

    def fake_run_legacy_pass1(**kwargs: object) -> FakeLegacyResult:
        captured.update(kwargs)
        return FakeLegacyResult()

    monkeypatch.setattr(api, "run_legacy_pass1", fake_run_legacy_pass1)

    request = CalibrationRunRequest(
        output_root=tmp_path,
        extra_args=("--sample",),
        timeout_seconds=30,
        dry_run=True,
    )
    result = run_calibration(request)

    assert result.implementation == "legacy-pass1"
    assert result.succeeded is True
    assert captured["output_root"] == tmp_path
    assert captured["extra_args"] == ("--sample",)
    assert captured["timeout_seconds"] == 30
    assert captured["dry_run"] is True


def test_runner_rejects_mismatched_request(tmp_path: Path) -> None:
    runner = LegacyPass1CalibrationRunner()
    request = CalibrationRunRequest(
        output_root=tmp_path,
        implementation="modern-pass2",
    )
    with pytest.raises(ValueError, match="incompatible implementation"):
        runner.run(request)
