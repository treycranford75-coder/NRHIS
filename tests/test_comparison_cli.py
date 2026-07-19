import sys
from pathlib import Path

import pytest

from nrhis_calibration import comparison_cli
from nrhis_calibration.reference_cases import write_reference_case


def test_comparison_cli_returns_zero_for_match(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    reference = case_dir / "metadata.json"
    reference.write_text('{"value": 1}\n', encoding="utf-8")
    manifest = case_dir / "case.json"
    write_reference_case(
        manifest,
        case_id="cli-compare",
        implementation="legacy-pass1",
        approved=True,
        description="CLI comparison case",
        artifacts=[(reference, "application/json")],
    )

    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "metadata.json").write_text('{"value": 1}\n', encoding="utf-8")
    output_path = tmp_path / "report.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "comparison_cli",
            str(manifest),
            str(candidate),
            "--json-output",
            str(output_path),
        ],
    )

    assert comparison_cli.main() == 0
    output = capsys.readouterr().out
    assert "Matched: True" in output
    assert output_path.is_file()
