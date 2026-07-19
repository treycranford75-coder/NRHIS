import json
from pathlib import Path

import pytest

from nrhis_calibration.archive_retention import (
    ArchiveRetentionDecision,
    ArchiveRetentionPlan,
    write_retention_plan,
)
from nrhis_calibration.archive_retention_action import (
    ArchiveRetentionActionError,
    build_action_manifest,
    validate_action_manifest,
    write_action_manifest,
)
from nrhis_calibration.archive_retention_approval import (
    approve_retention_plan,
    write_retention_approval,
)


def _inputs(tmp_path: Path) -> tuple[Path, Path]:
    plan = ArchiveRetentionPlan(
        generated_at_utc="2026-07-18T12:00:00+00:00",
        retain_latest=1,
        decisions=(
            ArchiveRetentionDecision(
                archive_id="latest",
                manifest_path="latest/manifest.json",
                action="retain",
                reason="latest valid archive",
            ),
            ArchiveRetentionDecision(
                archive_id="broken",
                manifest_path="broken/manifest.json",
                action="quarantine",
                reason="archive validation failed",
            ),
        ),
    )
    plan_path = tmp_path / "plan.json"
    write_retention_plan(plan, plan_path)

    approval = approve_retention_plan(
        plan_path=plan_path,
        reviewer="Reviewer",
        rationale="Approved for dry-run action generation.",
        approved_actions=("retain", "quarantine"),
    )
    approval_path = tmp_path / "approval.json"
    write_retention_approval(approval, approval_path)
    return plan_path, approval_path


def test_build_and_validate_action_manifest(tmp_path: Path) -> None:
    plan, approval = _inputs(tmp_path)
    manifest = build_action_manifest(
        plan_path=plan,
        approval_path=approval,
    )
    output = tmp_path / "actions.json"
    write_action_manifest(manifest, output)

    validated = validate_action_manifest(
        plan_path=plan,
        approval_path=approval,
        action_manifest_path=output,
    )

    assert validated.dry_run is True
    assert len(validated.actions) == 2


def test_action_manifest_detects_approval_change(tmp_path: Path) -> None:
    plan, approval = _inputs(tmp_path)
    manifest = build_action_manifest(
        plan_path=plan,
        approval_path=approval,
    )
    output = tmp_path / "actions.json"
    write_action_manifest(manifest, output)

    approval.write_text("{}\n", encoding="utf-8")

    with pytest.raises(Exception):
        validate_action_manifest(
            plan_path=plan,
            approval_path=approval,
            action_manifest_path=output,
        )


def test_action_manifest_detects_action_count_change(tmp_path: Path) -> None:
    plan, approval = _inputs(tmp_path)
    manifest = build_action_manifest(
        plan_path=plan,
        approval_path=approval,
    )
    output = tmp_path / "actions.json"
    write_action_manifest(manifest, output)

    document = json.loads(output.read_text(encoding="utf-8"))
    document["action_count"] = 99
    output.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ArchiveRetentionActionError,
        match="Action count mismatch",
    ):
        validate_action_manifest(
            plan_path=plan,
            approval_path=approval,
            action_manifest_path=output,
        )
