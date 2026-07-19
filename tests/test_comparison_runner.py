import json
from pathlib import Path

import pytest

from nrhis_calibration.comparison_runner import (
    ComparisonRunnerError,
    compare_reference_case,
    write_comparison_report,
)
from nrhis_calibration.reference_cases import write_reference_case


def _create_case(tmp_path: Path, *, approved: bool = True) -> Path:
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    metadata = case_dir / "metadata.json"
    metadata.write_text(
        json.dumps({"value": 42.0, "run_id": "REFERENCE"}) + "\n",
        encoding="utf-8",
    )
    table = case_dir / "observations.csv"
    table.write_text(
        "station_id,timestamp_utc,flow_cfs\nA,2026-07-18T00:00:00Z,25.0\n",
        encoding="utf-8",
    )
    manifest = case_dir / "case.json"
    write_reference_case(
        manifest,
        case_id="comparison-case",
        implementation="legacy-pass1",
        approved=approved,
        description="Comparison test case",
        artifacts=[
            (metadata, "application/json"),
            (table, "text/csv"),
        ],
        ignored_json_keys=("run_id",),
        csv_key_columns=("station_id", "timestamp_utc"),
    )
    return manifest


def test_matching_candidate_passes(tmp_path: Path) -> None:
    manifest = _create_case(tmp_path)
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "metadata.json").write_text(
        json.dumps({"value": 42.0, "run_id": "CANDIDATE"}) + "\n",
        encoding="utf-8",
    )
    (candidate / "observations.csv").write_text(
        "station_id,timestamp_utc,flow_cfs\nA,2026-07-18T00:00:00Z,25.0\n",
        encoding="utf-8",
    )

    report = compare_reference_case(manifest, candidate_root=candidate)
    assert report.matched
    assert all(item.matched for item in report.artifact_reports)


def test_difference_is_reported(tmp_path: Path) -> None:
    manifest = _create_case(tmp_path)
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "metadata.json").write_text(
        json.dumps({"value": 99.0, "run_id": "CANDIDATE"}) + "\n",
        encoding="utf-8",
    )
    (candidate / "observations.csv").write_text(
        "station_id,timestamp_utc,flow_cfs\nA,2026-07-18T00:00:00Z,25.0\n",
        encoding="utf-8",
    )

    report = compare_reference_case(manifest, candidate_root=candidate)
    assert not report.matched
    assert any(not item.matched for item in report.artifact_reports)


def test_missing_candidate_artifact_is_reported(tmp_path: Path) -> None:
    manifest = _create_case(tmp_path)
    candidate = tmp_path / "candidate"
    candidate.mkdir()

    report = compare_reference_case(manifest, candidate_root=candidate)
    assert not report.matched
    assert any(
        difference.reason == "candidate artifact missing"
        for item in report.artifact_reports
        for difference in item.differences
    )


def test_unapproved_case_is_rejected_by_default(tmp_path: Path) -> None:
    manifest = _create_case(tmp_path, approved=False)
    candidate = tmp_path / "candidate"
    candidate.mkdir()

    with pytest.raises(Exception, match="is not approved"):
        compare_reference_case(manifest, candidate_root=candidate)


def test_missing_candidate_directory_is_rejected(tmp_path: Path) -> None:
    manifest = _create_case(tmp_path)
    with pytest.raises(ComparisonRunnerError, match="Candidate directory is missing"):
        compare_reference_case(
            manifest,
            candidate_root=tmp_path / "missing",
        )


def test_write_comparison_report(tmp_path: Path) -> None:
    manifest = _create_case(tmp_path)
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "metadata.json").write_text(
        json.dumps({"value": 42.0, "run_id": "CANDIDATE"}) + "\n",
        encoding="utf-8",
    )
    (candidate / "observations.csv").write_text(
        "station_id,timestamp_utc,flow_cfs\nA,2026-07-18T00:00:00Z,25.0\n",
        encoding="utf-8",
    )
    report = compare_reference_case(manifest, candidate_root=candidate)
    output = tmp_path / "comparison.json"
    write_comparison_report(report, output)
    document = json.loads(output.read_text(encoding="utf-8"))
    assert document["matched"] is True
    assert document["case_id"] == "comparison-case"
