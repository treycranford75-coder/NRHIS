from pathlib import Path

import pytest

from nrhis_calibration.characterization import NumericTolerance
from nrhis_calibration.reference_cases import (
    ReferenceCaseError,
    load_reference_case,
    validate_reference_case,
    write_reference_case,
)


def test_write_load_and_validate_reference_case(tmp_path: Path) -> None:
    artifact = tmp_path / "reference.json"
    artifact.write_text('{"value": 42}\n', encoding="utf-8")
    manifest = tmp_path / "case.json"

    write_reference_case(
        manifest,
        case_id="synthetic-001",
        implementation="legacy-pass1",
        approved=False,
        description="Synthetic reference case",
        artifacts=[(artifact, "application/json")],
        ignored_json_keys=("run_id",),
        numeric_tolerances={"value": NumericTolerance(absolute=0.01)},
    )

    reference_case = load_reference_case(manifest)
    assert reference_case.case_id == "synthetic-001"
    assert reference_case.approved is False
    assert validate_reference_case(
        reference_case,
        manifest_directory=tmp_path,
    ) == ("reference.json",)


def test_require_approved_rejects_unapproved_case(tmp_path: Path) -> None:
    artifact = tmp_path / "reference.json"
    artifact.write_text("{}\n", encoding="utf-8")
    manifest = tmp_path / "case.json"

    write_reference_case(
        manifest,
        case_id="synthetic-002",
        implementation="legacy-pass1",
        approved=False,
        description="Synthetic reference case",
        artifacts=[(artifact, "application/json")],
    )
    reference_case = load_reference_case(manifest)

    with pytest.raises(ReferenceCaseError, match="is not approved"):
        validate_reference_case(
            reference_case,
            manifest_directory=tmp_path,
            require_approved=True,
        )


def test_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    artifact = tmp_path / "reference.json"
    artifact.write_text("{}\n", encoding="utf-8")
    manifest = tmp_path / "case.json"

    write_reference_case(
        manifest,
        case_id="synthetic-003",
        implementation="legacy-pass1",
        approved=True,
        description="Synthetic reference case",
        artifacts=[(artifact, "application/json")],
    )
    artifact.write_text('{"changed": true}\n', encoding="utf-8")
    reference_case = load_reference_case(manifest)

    with pytest.raises(ReferenceCaseError, match="hash mismatch"):
        validate_reference_case(
            reference_case,
            manifest_directory=tmp_path,
        )


def test_missing_artifact_is_rejected(tmp_path: Path) -> None:
    manifest = tmp_path / "case.json"
    manifest.write_text(
        """{
  "approved": true,
  "artifacts": [
    {
      "media_type": "application/json",
      "path": "missing.json",
      "sha256": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    }
  ],
  "case_id": "synthetic-004",
  "csv_key_columns": [],
  "description": "Synthetic reference case",
  "ignored_json_keys": [],
  "implementation": "legacy-pass1",
  "numeric_tolerances": {}
}
""",
        encoding="utf-8",
    )
    reference_case = load_reference_case(manifest)

    with pytest.raises(ReferenceCaseError, match="is missing"):
        validate_reference_case(
            reference_case,
            manifest_directory=tmp_path,
        )
