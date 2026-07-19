import sys
from pathlib import Path

import pytest

from nrhis_calibration import archive_retention_action_cli
from nrhis_calibration.archive_retention import (
    ArchiveRetentionDecision,
    ArchiveRetentionPlan,
    write_retention_plan,
)
from nrhis_calibration.archive_retention_approval import (
    approve_retention_plan,
    write_retention_approval,
)


def test_action_cli_create_and_validate(
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

    output = tmp_path / "actions.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "archive_retention_action_cli",
            "create",
            str(plan_path),
            str(approval_path),
            str(output),
        ],
    )
    assert archive_retention_action_cli.main() == 0
    assert "Dry run: True" in capsys.readouterr().out

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "archive_retention_action_cli",
            "validate",
            str(plan_path),
            str(approval_path),
            str(output),
        ],
    )
    assert archive_retention_action_cli.main() == 0
    assert "Action manifest valid: True" in capsys.readouterr().out
