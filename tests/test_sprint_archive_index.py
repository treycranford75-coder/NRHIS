import json
from pathlib import Path

from nrhis_calibration.sprint_archive import create_sprint_archive
from nrhis_calibration.sprint_archive_index import (
    build_sprint_archive_index,
    discover_sprint_archive_manifests,
    filter_sprint_archive_index,
    write_sprint_archive_index,
)


def _create_archive(
    tmp_path: Path,
    *,
    archive_id: str,
    sprint: str,
) -> Path:
    source_dir = tmp_path / f"source-{archive_id}"
    source_dir.mkdir()

    inventory = source_dir / "inventory.json"
    inventory.write_text("[]\n", encoding="utf-8")

    closeout = source_dir / "closeout.json"
    closeout.write_text(
        json.dumps({"accepted": True}) + "\n",
        encoding="utf-8",
    )

    archive = create_sprint_archive(
        destination_root=tmp_path / "archives",
        archive_id=archive_id,
        release_inventory=inventory,
        closeout_report=closeout,
        metadata={"sprint": sprint},
    )
    return Path(archive.manifest_path)


def test_discover_and_build_archive_index(tmp_path: Path) -> None:
    _create_archive(tmp_path, archive_id="sprint2-a", sprint="Sprint 2")
    _create_archive(tmp_path, archive_id="sprint3-a", sprint="Sprint 3")

    manifests = discover_sprint_archive_manifests(tmp_path / "archives")
    assert len(manifests) == 2

    index = build_sprint_archive_index(tmp_path / "archives")
    assert len(index.entries) == 2
    assert all(entry.valid for entry in index.entries)


def test_invalid_archive_remains_visible(tmp_path: Path) -> None:
    manifest = _create_archive(
        tmp_path,
        archive_id="broken",
        sprint="Sprint 2",
    )
    artifact = manifest.parent / "artifacts" / "release_inventory.json"
    artifact.write_text("[1]\n", encoding="utf-8")

    index = build_sprint_archive_index(tmp_path / "archives")
    assert len(index.entries) == 1
    assert index.entries[0].valid is False
    assert index.entries[0].validation_error


def test_filter_archive_index(tmp_path: Path) -> None:
    _create_archive(tmp_path, archive_id="sprint2-a", sprint="Sprint 2")
    _create_archive(tmp_path, archive_id="sprint3-a", sprint="Sprint 3")

    index = build_sprint_archive_index(tmp_path / "archives")

    sprint2 = filter_sprint_archive_index(index, sprint="SPRINT 2")
    assert [entry.archive_id for entry in sprint2.entries] == ["sprint2-a"]

    valid = filter_sprint_archive_index(index, valid=True)
    assert len(valid.entries) == 2


def test_write_archive_index_json(tmp_path: Path) -> None:
    _create_archive(tmp_path, archive_id="sprint2-a", sprint="Sprint 2")
    index = build_sprint_archive_index(tmp_path / "archives")
    output = tmp_path / "archive-index.json"

    write_sprint_archive_index(index, output)

    document = json.loads(output.read_text(encoding="utf-8"))
    assert document["archive_count"] == 1
    assert document["entries"][0]["archive_id"] == "sprint2-a"
