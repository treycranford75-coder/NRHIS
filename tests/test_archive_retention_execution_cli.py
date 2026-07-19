import sys
from pathlib import Path

import pytest

from nrhis_calibration import archive_retention_execution_cli
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


def test_execution_cli_simulate_and_validate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plan = ArchiveRetentionPlan(
        generated_at_utc="2026-07-18T12:00:00+00:00",
        retain_latest=1,
        decisions=(
            ArchiveRetentionDecision(
                archive_id="latest",
                manifest_path="latest/manifest.json",
                action="retain",
                reason="latest",
            ),
        ),
    )
    plan_path = tmp_path / "plan.json"
    write_retention_plan(plan, plan_path)

    approval = approve_retention_plan(
        plan_path=plan_path,
        reviewer="Reviewer",
        rationale="Approved.",
        approved_actions=("retain",),
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

    output = tmp_path / "execution.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "archive_retention_execution_cli",
            "simulate",
            str(plan_path),
            str(approval_path),
            str(action_path),
            str(output),
        ],
    )
    assert archive_retention_execution_cli.main() == 0
    assert "Executed: False" in capsys.readouterr().out

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "archive_retention_execution_cli",
            "validate",
            str(output),
        ],
    )
    assert archive_retention_execution_cli.main() == 0
    assert "Execution report valid: True" in capsys.readouterr().out
