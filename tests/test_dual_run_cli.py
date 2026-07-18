import sys
from pathlib import Path

import pytest

from nrhis_calibration import dual_run_cli
from nrhis_calibration.api import CalibrationRunResult
from nrhis_calibration.comparison_runner import ReferenceComparisonReport
from nrhis_calibration.dual_run import DualRunResult


def test_dual_run_cli_returns_zero_for_match(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = DualRunResult(
        case_id="cli-case",
        implementation="legacy-pass1",
        run_result=CalibrationRunResult(
            implementation="legacy-pass1",
            run_id="RUN-001",
            return_code=0,
            succeeded=True,
            metadata_path=str(tmp_path / "metadata.json"),
            stdout_path=str(tmp_path / "stdout.log"),
            stderr_path=str(tmp_path / "stderr.log"),
        ),
        comparison_report=ReferenceComparisonReport(
            case_id="cli-case",
            implementation="legacy-pass1",
            matched=True,
            artifact_reports=(),
        ),
        matched=True,
        comparison_report_path=str(tmp_path / "comparison_report.json"),
    )

    monkeypatch.setattr(
        dual_run_cli,
        "run_dual_verification",
        lambda **kwargs: result,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dual_run_cli",
            "case.json",
            "output",
            "--summary-output",
            str(tmp_path / "summary.json"),
        ],
    )

    assert dual_run_cli.main() == 0
    output = capsys.readouterr().out
    assert "Matched: True" in output
    assert "Run ID: RUN-001" in output
