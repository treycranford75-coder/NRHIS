import sys
from pathlib import Path

import pytest

from nrhis_calibration import reference_cli
from nrhis_calibration.reference_cases import write_reference_case


def test_reference_cli_reports_verified_case(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    artifact = tmp_path / "reference.json"
    artifact.write_text("{}\n", encoding="utf-8")
    manifest = tmp_path / "case.json"

    write_reference_case(
        manifest,
        case_id="synthetic-cli",
        implementation="legacy-pass1",
        approved=True,
        description="Synthetic CLI case",
        artifacts=[(artifact, "application/json")],
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["reference_cli", str(manifest), "--require-approved"],
    )

    assert reference_cli.main() == 0
    output = capsys.readouterr().out
    assert "Case ID: synthetic-cli" in output
    assert "Approved: True" in output
    assert "Verified artifacts: 1" in output
