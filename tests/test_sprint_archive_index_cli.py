import sys
from pathlib import Path

import pytest

from nrhis_calibration import sprint_archive_index_cli
from nrhis_calibration.sprint_archive_index import (
    SprintArchiveIndex,
    SprintArchiveIndexEntry,
)


def test_archive_index_cli_reports_archives(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    index = SprintArchiveIndex(
        root=str(tmp_path),
        entries=(
            SprintArchiveIndexEntry(
                archive_id="sprint2-closeout",
                manifest_path=str(tmp_path / "manifest.json"),
                valid=True,
                artifact_count=2,
                metadata={"sprint": "Sprint 2"},
            ),
        ),
    )

    monkeypatch.setattr(
        sprint_archive_index_cli,
        "build_sprint_archive_index",
        lambda archive_root: index,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "sprint_archive_index_cli",
            str(tmp_path),
            "--valid-only",
            "--sprint",
            "Sprint 2",
            "--json-output",
            str(tmp_path / "index.json"),
        ],
    )

    assert sprint_archive_index_cli.main() == 0
    output = capsys.readouterr().out
    assert "Archives: 1" in output
    assert "sprint2-closeout" in output
