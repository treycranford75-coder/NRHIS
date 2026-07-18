import sys
from pathlib import Path

import pytest

from nrhis_calibration import reference_approval_cli
from nrhis_calibration.reference_cases import write_reference_case


def test_approval_cli_approves_case(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    artifact = tmp_path / "reference.json"
    artifact.write_text("{}\n", encoding="utf-8")
    manifest = tmp_path / "case.json"
    write_reference_case(
        manifest,
        case_id="cli-approval",
        implementation="legacy-pass1",
        approved=False,
        description="CLI approval test",
        artifacts=[(artifact, "application/json")],
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "reference_approval_cli",
            "approve",
            str(manifest),
            "--reviewer",
            "QA Reviewer",
            "--rationale",
            "Reviewed and accepted.",
        ],
    )

    assert reference_approval_cli.main() == 0
    output = capsys.readouterr().out
    assert "Case ID: cli-approval" in output
    assert "Action: approve" in output
    assert "Reviewer: QA Reviewer" in output
