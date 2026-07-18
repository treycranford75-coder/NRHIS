from pathlib import Path

import pytest

from nrhis_calibration import dual_run
from nrhis_calibration.api import CalibrationRunResult
from nrhis_calibration.comparison_runner import ReferenceComparisonReport


def _run_result(tmp_path: Path, *, succeeded: bool = True) -> CalibrationRunResult:
    run_directory = tmp_path / "run"
    run_directory.mkdir()
    metadata_path = run_directory / "metadata.json"
    metadata_path.write_text("{}\n", encoding="utf-8")
    (run_directory / "stdout.log").write_text("", encoding="utf-8")
    (run_directory / "stderr.log").write_text("", encoding="utf-8")

    return CalibrationRunResult(
        implementation="legacy-pass1",
        run_id="20260718T180000Z",
        return_code=0 if succeeded else 2,
        succeeded=succeeded,
        metadata_path=str(metadata_path),
        stdout_path=str(run_directory / "stdout.log"),
        stderr_path=str(run_directory / "stderr.log"),
    )


def test_dual_run_executes_and_compares(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run_result = _run_result(tmp_path)
    comparison = ReferenceComparisonReport(
        case_id="approved-case",
        implementation="legacy-pass1",
        matched=True,
        artifact_reports=(),
    )

    monkeypatch.setattr(dual_run, "run_calibration", lambda request: run_result)
    monkeypatch.setattr(
        dual_run,
        "compare_reference_case",
        lambda *args, **kwargs: comparison,
    )

    result = dual_run.run_dual_verification(
        manifest_path=tmp_path / "case.json",
        output_root=tmp_path / "output",
    )

    assert result.matched is True
    assert result.case_id == "approved-case"
    assert Path(result.comparison_report_path).name == "comparison_report.json"


def test_dual_run_rejects_failed_calibration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        dual_run,
        "run_calibration",
        lambda request: _run_result(tmp_path, succeeded=False),
    )

    with pytest.raises(dual_run.DualRunError, match="Calibration run failed"):
        dual_run.run_dual_verification(
            manifest_path=tmp_path / "case.json",
            output_root=tmp_path / "output",
        )


def test_dual_run_writes_summary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run_result = _run_result(tmp_path)
    comparison = ReferenceComparisonReport(
        case_id="approved-case",
        implementation="legacy-pass1",
        matched=False,
        artifact_reports=(),
    )

    monkeypatch.setattr(dual_run, "run_calibration", lambda request: run_result)
    monkeypatch.setattr(
        dual_run,
        "compare_reference_case",
        lambda *args, **kwargs: comparison,
    )

    result = dual_run.run_dual_verification(
        manifest_path=tmp_path / "case.json",
        output_root=tmp_path / "output",
    )
    destination = tmp_path / "dual-run-summary.json"
    dual_run.write_dual_run_summary(result, destination)

    content = destination.read_text(encoding="utf-8")
    assert '"matched": false' in content
    assert '"case_id": "approved-case"' in content
