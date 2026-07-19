import json
from pathlib import Path

import pytest

from nrhis_calibration.reference_approval import (
    ReferenceApprovalError,
    approve_reference_case,
    revoke_reference_case,
)
from nrhis_calibration.reference_cases import (
    load_reference_case,
    write_reference_case,
)


def _create_unapproved_case(tmp_path: Path) -> Path:
    artifact = tmp_path / "reference.json"
    artifact.write_text('{"value": 42}\n', encoding="utf-8")
    manifest = tmp_path / "case.json"
    write_reference_case(
        manifest,
        case_id="approval-case",
        implementation="legacy-pass1",
        approved=False,
        description="Approval test case",
        artifacts=[(artifact, "application/json")],
    )
    return manifest


def test_approve_valid_case(tmp_path: Path) -> None:
    manifest = _create_unapproved_case(tmp_path)

    record = approve_reference_case(
        manifest,
        reviewer="Reviewer One",
        rationale="Artifacts and provenance reviewed.",
    )

    assert record.action == "approve"
    assert load_reference_case(manifest).approved is True
    approval_record = json.loads(
        (tmp_path / "approval_record.json").read_text(encoding="utf-8")
    )
    assert approval_record["reviewer"] == "Reviewer One"


def test_approve_rejects_already_approved_case(tmp_path: Path) -> None:
    manifest = _create_unapproved_case(tmp_path)
    approve_reference_case(
        manifest,
        reviewer="Reviewer One",
        rationale="Initial approval.",
    )

    with pytest.raises(ReferenceApprovalError, match="already approved"):
        approve_reference_case(
            manifest,
            reviewer="Reviewer Two",
            rationale="Duplicate approval.",
        )


def test_approve_rejects_invalid_artifact_hash(tmp_path: Path) -> None:
    manifest = _create_unapproved_case(tmp_path)
    (tmp_path / "reference.json").write_text('{"value": 99}\n', encoding="utf-8")

    with pytest.raises(Exception, match="hash mismatch"):
        approve_reference_case(
            manifest,
            reviewer="Reviewer One",
            rationale="Should fail.",
        )


def test_revoke_approved_case(tmp_path: Path) -> None:
    manifest = _create_unapproved_case(tmp_path)
    approve_reference_case(
        manifest,
        reviewer="Reviewer One",
        rationale="Initial approval.",
    )

    record = revoke_reference_case(
        manifest,
        reviewer="Reviewer Two",
        rationale="Superseded by a corrected case.",
    )

    assert record.action == "revoke"
    assert load_reference_case(manifest).approved is False
    revocation_record = json.loads(
        (tmp_path / "revocation_record.json").read_text(encoding="utf-8")
    )
    assert revocation_record["reviewer"] == "Reviewer Two"


def test_revoke_rejects_unapproved_case(tmp_path: Path) -> None:
    manifest = _create_unapproved_case(tmp_path)

    with pytest.raises(ReferenceApprovalError, match="is not approved"):
        revoke_reference_case(
            manifest,
            reviewer="Reviewer One",
            rationale="Nothing to revoke.",
        )
