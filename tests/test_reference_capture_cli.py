import json
import sys
from pathlib import Path

import pytest

from nrhis_calibration import reference_capture_cli


def test_capture_cli_reports_unapproved_case(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run_directory = tmp_path / "run"
    run_directory.mkdir()

    metadata = {
        "run_id": "20260718T170000Z",
        "return_code": 0,
        "succeeded": True,
    }
    (run_directory / "metadata.json").write_text(
        json.dumps(metadata) + "\n",
        encoding="utf-8",
    )
    (run_directory / "stdout.log").write_text("ok\n", encoding="utf-8")
    (run_directory / "stderr.log").write_text("", encoding="utf-8")

    reference_root = tmp_path / "references"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "reference_capture_cli",
            str(run_directory),
            str(reference_root),
            "cli-case",
            "--description",
            "CLI capture case",
        ],
    )

    assert reference_capture_cli.main() == 0
    output = capsys.readouterr().out
    assert "Case directory:" in output
    assert "Captured artifacts: 4" in output
    assert "Approval state: False" in output
