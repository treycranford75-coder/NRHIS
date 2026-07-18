import sys
from pathlib import Path
import pytest
from nrhis_calibration import archive_retention_cli
from nrhis_calibration.sprint_archive_index import SprintArchiveIndex, SprintArchiveIndexEntry

def test_archive_retention_cli_generates_plan(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    index = SprintArchiveIndex(
        root=str(tmp_path),
        entries=(
            SprintArchiveIndexEntry(
                "sprint2-closeout",
                str(tmp_path / "manifest.json"),
                True,
                2,
                {"created_at_utc": "2026-07-18T10:00:00+00:00"},
            ),
        ),
    )
    monkeypatch.setattr(archive_retention_cli, "build_sprint_archive_index", lambda archive_root: index)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "archive_retention_cli",
            str(tmp_path),
            "--retain-latest",
            "1",
            "--json-output",
            str(tmp_path / "retention.json"),
        ],
    )
    assert archive_retention_cli.main() == 0
    output = capsys.readouterr().out
    assert "Retain: 1" in output
    assert "Quarantine: 0" in output
