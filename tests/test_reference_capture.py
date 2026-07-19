import json
from pathlib import Path

import pytest

from nrhis_calibration.reference_capture import (
    ReferenceCaptureError,
    capture_reference_case,
)
from nrhis_calibration.reference_cases import (
    load_reference_case,
    validate_reference_case,
)


def _write_successful_run(run_directory: Path) -> None:
    run_directory.mkdir()
    metadata = {
        "run_id": "20260718T160000Z",
        "return_code": 0,
        "succeeded": True,
        "started_at_utc": "2026-07-18T16:00:00+00:00",
        "finished_at_utc": "2026-07-18T16:00:01+00:00",
        "duration_seconds": 1.0,
        "stdout_path": "stdout.log",
        "stderr_path": "stderr.log",
        "metadata_path": "metadata.json",
    }
    (run_directory / "metadata.json").write_text(
        json.dumps(metadata) + "\n",
        encoding="utf-8",
    )
    (run_directory / "stdout.log").write_text("ok\n", encoding="utf-8")
    (run_directory / "stderr.log").write_text("", encoding="utf-8")


def test_capture_creates_unapproved_valid_case(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    reference_root = tmp_path / "references"
    _write_successful_run(run_directory)

    result = capture_reference_case(
        run_directory=run_directory,
        reference_root=reference_root,
        case_id="legacy-pass1-smoke-001",
        description="Synthetic successful legacy run",
    )

    manifest = Path(result.manifest_path)
    reference_case = load_reference_case(manifest)

    assert reference_case.approved is False
    assert reference_case.case_id == "legacy-pass1-smoke-001"
    assert len(reference_case.artifacts) == 4
    assert validate_reference_case(
        reference_case,
        manifest_directory=manifest.parent,
    ) == (
        "artifacts/metadata.json",
        "artifacts/stdout.log",
        "artifacts/stderr.log",
        "capture_record.json",
    )


def test_capture_rejects_failed_run(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    _write_successful_run(run_directory)

    metadata_path = run_directory / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["return_code"] = 2
    metadata["succeeded"] = False
    metadata_path.write_text(json.dumps(metadata) + "\n", encoding="utf-8")

    with pytest.raises(ReferenceCaptureError, match="Only successful"):
        capture_reference_case(
            run_directory=run_directory,
            reference_root=tmp_path / "references",
            case_id="failed-run",
            description="Failed run",
        )


def test_capture_refuses_overwrite(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    reference_root = tmp_path / "references"
    _write_successful_run(run_directory)

    capture_reference_case(
        run_directory=run_directory,
        reference_root=reference_root,
        case_id="duplicate",
        description="First capture",
    )

    with pytest.raises(ReferenceCaptureError, match="will not be overwritten"):
        capture_reference_case(
            run_directory=run_directory,
            reference_root=reference_root,
            case_id="duplicate",
            description="Second capture",
        )


def test_capture_rejects_missing_artifact(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    _write_successful_run(run_directory)
    (run_directory / "stderr.log").unlink()

    with pytest.raises(ReferenceCaptureError, match="Required run artifact is missing"):
        capture_reference_case(
            run_directory=run_directory,
            reference_root=tmp_path / "references",
            case_id="missing-artifact",
            description="Missing artifact",
        )
