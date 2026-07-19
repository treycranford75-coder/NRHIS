import json
from pathlib import Path

import pytest

from nrhis_calibration.archive_retention import (
    ArchiveRetentionDecision,
    ArchiveRetentionPlan,
    write_retention_plan,
)
from nrhis_calibration.archive_retention_action import (
    build_action_manifest,
    write_action_manifest,
)
from nrhis_calibration.archive_retention_approval import (
    approve_retention_plan,
    write_retention_approval,
)
from nrhis_calibration.archive_retention_execution import (
    ArchiveRetentionExecutionError,
    simulate_retention_execution,
    validate_execution_report,
    write_execution_report,
)


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
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
        rationale="Approved for dry-run simulation.",
        approved_actions=("retain", "quarantine"),
    )
    approval_path = tmp_path / "approval.json"
    write_retention_approval(approval, approval_path)

    action_manifest = build_action_manifest(
        plan_path=plan_path,
        approval_path=approval_path,
        dry_run=True,
    )
    action_path = tmp_path / "actions.json"
    write_action_manifest(action_manifest, action_path)

    return plan_path, approval_path, action_path


def test_simulate_and_validate_execution(tmp_path: Path) -> None:
    plan, approval, actions = _inputs(tmp_path)

    report = simulate_retention_execution(
        plan_path=plan,
        approval_path=approval,
        action_manifest_path=actions,
    )
    output = tmp_path / "execution.json"
    write_execution_report(report, output)

    validated = validate_execution_report(output)

    assert validated.dry_run is True
    assert validated.executed is False
    assert validated.item_count == 2


def test_execution_rejects_live_manifest(tmp_path: Path) -> None:
    plan, approval, _ = _inputs(tmp_path)
    action_manifest = build_action_manifest(
        plan_path=plan,
        approval_path=approval,
        dry_run=False,
    )
    live_action_path = tmp_path / "live-actions.json"
    write_action_manifest(action_manifest, live_action_path)

    with pytest.raises(
        ArchiveRetentionExecutionError,
        match="dry-run action manifests only",
    ):
        simulate_retention_execution(
            plan_path=plan,
            approval_path=approval,
            action_manifest_path=live_action_path,
        )


def test_execution_report_rejects_executed_true(
    tmp_path: Path,
) -> None:
    report = tmp_path / "execution.json"
    report.write_text(
        json.dumps(
            {
                "dry_run": True,
                "executed": True,
                "item_count": 0,
                "items": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ArchiveRetentionExecutionError,
        match="must not indicate live execution",
    ):
        validate_execution_report(report)
