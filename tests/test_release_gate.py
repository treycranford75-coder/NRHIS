import json
from pathlib import Path

from nrhis_calibration.evidence_bundle import create_evidence_bundle
from nrhis_calibration.release_gate import (
    evaluate_release_gate,
    write_release_gate_report,
)


def _create_bundle(tmp_path: Path, *, matched: bool = True) -> Path:
    comparison = tmp_path / "comparison_report.json"
    dual_run = tmp_path / "dual_run_summary.json"
    comparison.write_text(
        json.dumps({"matched": matched}) + "\n",
        encoding="utf-8",
    )
    dual_run.write_text(
        json.dumps({"case_id": "case-1", "matched": matched}) + "\n",
        encoding="utf-8",
    )
    result = create_evidence_bundle(
        destination_root=tmp_path / "evidence",
        bundle_id="release-bundle",
        source_artifacts=[comparison, dual_run],
        metadata={"release": "rc15"},
    )
    return Path(result.manifest_path)


def test_release_gate_accepts_valid_matching_bundle(tmp_path: Path) -> None:
    manifest = _create_bundle(tmp_path, matched=True)

    report = evaluate_release_gate(
        release_id="v0.1.1-rc15+build015",
        evidence_manifest=manifest,
    )

    assert report.accepted is True
    assert all(check.passed for check in report.checks)


def test_release_gate_rejects_mismatch(tmp_path: Path) -> None:
    manifest = _create_bundle(tmp_path, matched=False)

    report = evaluate_release_gate(
        release_id="v0.1.1-rc15+build015",
        evidence_manifest=manifest,
    )

    assert report.accepted is False
    assert any(check.name == "comparison_matched" and not check.passed for check in report.checks)


def test_release_gate_rejects_missing_required_artifact(tmp_path: Path) -> None:
    comparison = tmp_path / "comparison_report.json"
    comparison.write_text('{"matched": true}\n', encoding="utf-8")
    result = create_evidence_bundle(
        destination_root=tmp_path / "evidence",
        bundle_id="incomplete",
        source_artifacts=[comparison],
        metadata={},
    )

    report = evaluate_release_gate(
        release_id="release-incomplete",
        evidence_manifest=result.manifest_path,
    )

    assert report.accepted is False
    assert any(
        check.name == "required_artifact:dual_run_summary.json" and not check.passed
        for check in report.checks
    )


def test_release_gate_report_json(tmp_path: Path) -> None:
    manifest = _create_bundle(tmp_path, matched=True)
    report = evaluate_release_gate(
        release_id="release-json",
        evidence_manifest=manifest,
    )
    destination = tmp_path / "release-gate.json"

    write_release_gate_report(report, destination)

    document = json.loads(destination.read_text(encoding="utf-8"))
    assert document["accepted"] is True
    assert document["release_id"] == "release-json"
