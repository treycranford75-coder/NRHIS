import json
import sys
from pathlib import Path

import pytest

from nrhis_calibration import sprint_closeout_cli


def test_sprint_closeout_cli_accepts_inventory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    inventory = tmp_path / "inventory.json"
    inventory.write_text(
        json.dumps(
            [
                {
                    "build_number": 15,
                    "tag": "v0.1.1-rc15+build015",
                    "commit": "eb8bdd1",
                    "title": "Release Acceptance Gate",
                    "test_count": 78,
                    "coverage_percent": 85.54,
                    "pre_release": True,
                }
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    output = tmp_path / "closeout.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "sprint_closeout_cli",
            str(inventory),
            "--first-build",
            "15",
            "--final-build",
            "15",
            "--json-output",
            str(output),
        ],
    )

    assert sprint_closeout_cli.main() == 0
    text = capsys.readouterr().out
    assert "Accepted: True" in text
    assert output.is_file()
