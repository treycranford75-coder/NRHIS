import json
from pathlib import Path

from nrhis_calibration.reference_catalog import (
    build_reference_catalog,
    discover_reference_manifests,
    filter_catalog,
    write_catalog_json,
)
from nrhis_calibration.reference_cases import write_reference_case


def _create_case(
    root: Path,
    case_id: str,
    *,
    approved: bool,
    implementation: str = "legacy-pass1",
) -> Path:
    case_directory = root / case_id
    case_directory.mkdir(parents=True)
    artifact = case_directory / "reference.json"
    artifact.write_text('{"value": 42}\n', encoding="utf-8")
    manifest = case_directory / "case.json"
    write_reference_case(
        manifest,
        case_id=case_id,
        implementation=implementation,
        approved=approved,
        description=f"Reference case {case_id}",
        artifacts=[(artifact, "application/json")],
    )
    return manifest


def test_discover_and_build_catalog(tmp_path: Path) -> None:
    _create_case(tmp_path, "case-a", approved=False)
    _create_case(tmp_path, "case-b", approved=True)

    manifests = discover_reference_manifests(tmp_path)
    assert len(manifests) == 2

    catalog = build_reference_catalog(tmp_path)
    assert len(catalog.entries) == 2
    assert {entry.case_id for entry in catalog.entries} == {"case-a", "case-b"}
    assert all(entry.valid for entry in catalog.entries)


def test_catalog_marks_invalid_case(tmp_path: Path) -> None:
    case_directory = tmp_path / "broken"
    case_directory.mkdir()
    (case_directory / "case.json").write_text("{not-json", encoding="utf-8")

    catalog = build_reference_catalog(tmp_path)
    assert len(catalog.entries) == 1
    assert catalog.entries[0].valid is False
    assert catalog.entries[0].validation_error


def test_filter_catalog(tmp_path: Path) -> None:
    _create_case(tmp_path, "legacy-approved", approved=True)
    _create_case(
        tmp_path,
        "modern-unapproved",
        approved=False,
        implementation="modern-pass2",
    )

    catalog = build_reference_catalog(tmp_path)

    approved = filter_catalog(catalog, approved=True)
    assert [entry.case_id for entry in approved.entries] == ["legacy-approved"]

    modern = filter_catalog(catalog, implementation="MODERN-PASS2")
    assert [entry.case_id for entry in modern.entries] == ["modern-unapproved"]


def test_write_catalog_json(tmp_path: Path) -> None:
    _create_case(tmp_path, "case-json", approved=True)
    catalog = build_reference_catalog(tmp_path)
    destination = tmp_path / "catalog.json"

    write_catalog_json(catalog, destination)

    document = json.loads(destination.read_text(encoding="utf-8"))
    assert document["entry_count"] == 1
    assert document["entries"][0]["case_id"] == "case-json"
