import json
from pathlib import Path

import pytest

from nrhis_calibration.sprint_archive import (
    SprintArchiveError,
    create_sprint_archive,
    validate_sprint_archive,
)


def _accepted_inputs(tmp_path: Path) -> tuple[Path, Path]:
    inventory = tmp_path / "inventory.json"
    inventory.write_text(
        '[{"build_number": 16, "tag": "v0.1.1-rc16+build016"}]\n',
        encoding="utf-8",
    )

    closeout = tmp_path / "closeout.json"
    closeout.write_text(
        json.dumps({"accepted": True, "release_count": 16}) + "\n",
        encoding="utf-8",
    )
    return inventory, closeout


def test_create_and_validate_sprint_archive(tmp_path: Path) -> None:
    inventory, closeout = _accepted_inputs(tmp_path)

    archive = create_sprint_archive(
        destination_root=tmp_path / "archives",
        archive_id="sprint2-closeout",
        release_inventory=inventory,
        closeout_report=closeout,
        metadata={"sprint": "Sprint 2"},
    )

    assert len(archive.artifacts) == 2
    assert validate_sprint_archive(archive.manifest_path) == (
        "artifacts/release_inventory.json",
        "artifacts/sprint_closeout.json",
    )


def test_rejects_unaccepted_closeout(tmp_path: Path) -> None:
    inventory, closeout = _accepted_inputs(tmp_path)
    closeout.write_text('{"accepted": false}\n', encoding="utf-8")

    with pytest.raises(SprintArchiveError, match="not accepted"):
        create_sprint_archive(
            destination_root=tmp_path / "archives",
            archive_id="rejected",
            release_inventory=inventory,
            closeout_report=closeout,
            metadata={},
        )


def test_refuses_archive_overwrite(tmp_path: Path) -> None:
    inventory, closeout = _accepted_inputs(tmp_path)

    create_sprint_archive(
        destination_root=tmp_path / "archives",
        archive_id="duplicate",
        release_inventory=inventory,
        closeout_report=closeout,
        metadata={},
    )

    with pytest.raises(SprintArchiveError, match="will not be overwritten"):
        create_sprint_archive(
            destination_root=tmp_path / "archives",
            archive_id="duplicate",
            release_inventory=inventory,
            closeout_report=closeout,
            metadata={},
        )


def test_detects_archive_tampering(tmp_path: Path) -> None:
    inventory, closeout = _accepted_inputs(tmp_path)

    archive = create_sprint_archive(
        destination_root=tmp_path / "archives",
        archive_id="tamper",
        release_inventory=inventory,
        closeout_report=closeout,
        metadata={},
    )

    copied_inventory = (
        Path(archive.archive_directory)
        / "artifacts"
        / "release_inventory.json"
    )
    copied_inventory.write_text("[]\n", encoding="utf-8")

    with pytest.raises(SprintArchiveError, match="mismatch"):
        validate_sprint_archive(archive.manifest_path)
