import sys
from pathlib import Path

import pytest

from nrhis_calibration import reference_catalog_cli
from nrhis_calibration.reference_cases import write_reference_case


def test_catalog_cli_reports_cases(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    case_directory = tmp_path / "case-one"
    case_directory.mkdir()
    artifact = case_directory / "reference.json"
    artifact.write_text("{}\n", encoding="utf-8")
    manifest = case_directory / "case.json"

    write_reference_case(
        manifest,
        case_id="case-one",
        implementation="legacy-pass1",
        approved=True,
        description="Catalog CLI case",
        artifacts=[(artifact, "application/json")],
    )

    output_path = tmp_path / "catalog.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "reference_catalog_cli",
            str(tmp_path),
            "--approved-only",
            "--valid-only",
            "--json-output",
            str(output_path),
        ],
    )

    assert reference_catalog_cli.main() == 0
    output = capsys.readouterr().out
    assert "Cases: 1" in output
    assert "case-one" in output
    assert output_path.is_file()
