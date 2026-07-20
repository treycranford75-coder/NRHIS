import json
import sys
from pathlib import Path

import pytest

from nrhis_calibration import sprint_archive_cli


def test_sprint_archive_cli_create_and_validate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    inventory = tmp_path / "inventory.json"
    inventory.write_text("[]\n", encoding="utf-8")

    closeout = tmp_path / "closeout.json"
    closeout.write_text(
        json.dumps({"accepted": True}) + "\n",
        encoding="utf-8",
    )

    archive_root = tmp_path / "archives"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "sprint_archive_cli",
            "create",
            str(archive_root),
            "sprint2-closeout",
            str(inventory),
            str(closeout),
            "--metadata-json",
            '{"sprint": "Sprint 2"}',
        ],
    )

    assert sprint_archive_cli.main() == 0
    create_output = capsys.readouterr().out
    assert "Artifacts: 2" in create_output

    manifest = archive_root / "sprint2-closeout" / "sprint_archive_manifest.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["sprint_archive_cli", "validate", str(manifest)],
    )

    assert sprint_archive_cli.main() == 0
    validate_output = capsys.readouterr().out
    assert "Verified artifacts: 2" in validate_output
