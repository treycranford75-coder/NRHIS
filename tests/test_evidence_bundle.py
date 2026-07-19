import json
from pathlib import Path

import pytest

from nrhis_calibration.evidence_bundle import (
    EvidenceBundleError,
    create_evidence_bundle,
    validate_evidence_bundle,
)


def test_create_and_validate_bundle(tmp_path: Path) -> None:
    first = tmp_path / "comparison_report.json"
    second = tmp_path / "dual_run_summary.json"
    first.write_text('{"matched": true}\n', encoding="utf-8")
    second.write_text('{"case_id": "case-1"}\n', encoding="utf-8")

    result = create_evidence_bundle(
        destination_root=tmp_path / "evidence",
        bundle_id="build014-case-1",
        source_artifacts=[first, second],
        metadata={"release": "rc14"},
    )

    assert result.artifact_count == 2
    assert validate_evidence_bundle(result.manifest_path) == (
        "artifacts/comparison_report.json",
        "artifacts/dual_run_summary.json",
    )

    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
    assert manifest["metadata"]["release"] == "rc14"


def test_bundle_refuses_overwrite(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.json"
    artifact.write_text("{}\n", encoding="utf-8")

    create_evidence_bundle(
        destination_root=tmp_path / "evidence",
        bundle_id="duplicate",
        source_artifacts=[artifact],
        metadata={},
    )

    with pytest.raises(EvidenceBundleError, match="will not be overwritten"):
        create_evidence_bundle(
            destination_root=tmp_path / "evidence",
            bundle_id="duplicate",
            source_artifacts=[artifact],
            metadata={},
        )


def test_bundle_rejects_missing_source(tmp_path: Path) -> None:
    with pytest.raises(EvidenceBundleError, match="is missing"):
        create_evidence_bundle(
            destination_root=tmp_path / "evidence",
            bundle_id="missing",
            source_artifacts=[tmp_path / "missing.json"],
            metadata={},
        )


def test_bundle_detects_hash_mismatch(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.json"
    artifact.write_text("{}\n", encoding="utf-8")

    result = create_evidence_bundle(
        destination_root=tmp_path / "evidence",
        bundle_id="tamper",
        source_artifacts=[artifact],
        metadata={},
    )

    copied = Path(result.bundle_directory) / "artifacts" / artifact.name
    copied.write_text('{"changed": true}\n', encoding="utf-8")

    with pytest.raises(EvidenceBundleError, match="mismatch"):
        validate_evidence_bundle(result.manifest_path)


def test_bundle_rejects_duplicate_filenames(tmp_path: Path) -> None:
    first_dir = tmp_path / "a"
    second_dir = tmp_path / "b"
    first_dir.mkdir()
    second_dir.mkdir()
    first = first_dir / "report.json"
    second = second_dir / "report.json"
    first.write_text("{}\n", encoding="utf-8")
    second.write_text("{}\n", encoding="utf-8")

    with pytest.raises(EvidenceBundleError, match="Duplicate evidence filename"):
        create_evidence_bundle(
            destination_root=tmp_path / "evidence",
            bundle_id="duplicate-name",
            source_artifacts=[first, second],
            metadata={},
        )
