import sys
from pathlib import Path

import pytest

from nrhis_calibration import archive_retention_approval_cli
from nrhis_calibration.archive_retention import (
    ArchiveRetentionDecision,
    ArchiveRetentionPlan,
    write_retention_plan,
)


def test_retention_approval_cli_approve_and_validate(
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
                reason="latest archive",
            ),
        ),
    )
    plan_path = tmp_path / "plan.json"
    approval_path = tmp_path / "approval.json"
    write_retention_plan(plan, plan_path)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "archive_retention_approval_cli",
            "approve",
            str(plan_path),
            str(approval_path),
            "--reviewer",
            "Trey Cranford",
            "--rationale",
            "Approved for controlled review.",
            "--approved-action",
            "retain",
        ],
    )

    assert archive_retention_approval_cli.main() == 0
    approve_output = capsys.readouterr().out
    assert "Reviewer: Trey Cranford" in approve_output

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "archive_retention_approval_cli",
            "validate",
            str(plan_path),
            str(approval_path),
        ],
    )

    assert archive_retention_approval_cli.main() == 0
    validate_output = capsys.readouterr().out
    assert "Approval valid: True" in validate_output
