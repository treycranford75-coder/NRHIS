import json
from pathlib import Path

import pytest

from nrhis_calibration.archive_retention import (
    ArchiveRetentionDecision,
    ArchiveRetentionPlan,
    write_retention_plan,
)
from nrhis_calibration.archive_retention_approval import (
    ArchiveRetentionApprovalError,
    approve_retention_plan,
    validate_retention_approval,
    write_retention_approval,
)


def _plan_file(tmp_path: Path) -> Path:
    plan = ArchiveRetentionPlan(
        generated_at_utc="2026-07-18T12:00:00+00:00",
        retain_latest=1,
        decisions=(
            ArchiveRetentionDecision(
                archive_id="latest",
                manifest_path="latest/manifest.json",
                action="retain",
                reason="within latest valid archive set",
            ),
            ArchiveRetentionDecision(
                archive_id="older",
                manifest_path="older/manifest.json",
                action="review",
                reason="outside latest valid archive set",
            ),
        ),
    )
    path = tmp_path / "retention-plan.json"
    write_retention_plan(plan, path)
    return path


def test_approve_and_validate_retention_plan(tmp_path: Path) -> None:
    plan = _plan_file(tmp_path)
    approval = approve_retention_plan(
        plan_path=plan,
        reviewer="Trey Cranford",
        rationale="Reviewed for Sprint 2 closeout.",
        approved_actions=("retain", "review"),
    )
    approval_path = tmp_path / "approval.json"
    write_retention_approval(approval, approval_path)

    validated = validate_retention_approval(
        plan_path=plan,
        approval_path=approval_path,
    )

    assert validated.reviewer == "Trey Cranford"
    assert validated.decision_count == 2


def test_approval_rejects_unapproved_action(tmp_path: Path) -> None:
    plan = _plan_file(tmp_path)

    with pytest.raises(
        ArchiveRetentionApprovalError,
        match="unapproved action",
    ):
        approve_retention_plan(
            plan_path=plan,
            reviewer="Reviewer",
            rationale="Partial approval.",
            approved_actions=("retain",),
        )


def test_approval_detects_plan_change(tmp_path: Path) -> None:
    plan = _plan_file(tmp_path)
    approval = approve_retention_plan(
        plan_path=plan,
        reviewer="Reviewer",
        rationale="Approved.",
        approved_actions=("retain", "review"),
    )
    approval_path = tmp_path / "approval.json"
    write_retention_approval(approval, approval_path)

    document = json.loads(plan.read_text(encoding="utf-8"))
    document["retain_latest"] = 2
    plan.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ArchiveRetentionApprovalError,
        match="hash does not match",
    ):
        validate_retention_approval(
            plan_path=plan,
            approval_path=approval_path,
        )


def test_approval_requires_reviewer_and_rationale(tmp_path: Path) -> None:
    plan = _plan_file(tmp_path)

    with pytest.raises(
        ArchiveRetentionApprovalError,
        match="reviewer",
    ):
        approve_retention_plan(
            plan_path=plan,
            reviewer="",
            rationale="Approved.",
        )

    with pytest.raises(
        ArchiveRetentionApprovalError,
        match="rationale",
    ):
        approve_retention_plan(
            plan_path=plan,
            reviewer="Reviewer",
            rationale="",
        )
