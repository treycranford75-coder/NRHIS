from pathlib import Path

import pytest

from nrhis_calibration.characterization import (
    NumericTolerance,
    compare_csv_rows,
    compare_json,
    load_csv_rows,
    load_json,
    sha256_file,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "calibration_characterization"


def test_reference_fixture_hash_is_stable() -> None:
    digest = sha256_file(FIXTURE_ROOT / "reference_metadata.json")
    assert len(digest) == 64
    assert digest == digest.upper()


def test_reference_json_matches_itself() -> None:
    document = load_json(FIXTURE_ROOT / "reference_metadata.json")
    report = compare_json(document, document)
    assert report.matched
    assert report.differences == ()


def test_json_numeric_tolerance_accepts_small_difference() -> None:
    expected = {"value": 100.0, "generated_at": "old"}
    actual = {"value": 100.04, "generated_at": "new"}

    report = compare_json(
        expected,
        actual,
        tolerance=NumericTolerance(absolute=0.05),
        ignored_keys=("generated_at",),
    )
    assert report.matched


def test_json_numeric_tolerance_reports_large_difference() -> None:
    report = compare_json(
        {"value": 100.0},
        {"value": 100.2},
        tolerance=NumericTolerance(absolute=0.05),
    )
    assert not report.matched
    assert report.differences[0].reason == "numeric tolerance exceeded"


def test_reference_csv_matches_with_numeric_tolerance() -> None:
    expected = load_csv_rows(FIXTURE_ROOT / "reference_observations.csv")
    actual = [dict(row) for row in expected]
    actual[0]["flow_cfs"] = "25.004"

    report = compare_csv_rows(
        expected,
        actual,
        key_columns=("station_id", "timestamp_utc"),
        numeric_columns={"flow_cfs": NumericTolerance(absolute=0.01)},
    )
    assert report.matched


def test_csv_reports_missing_row() -> None:
    expected = load_csv_rows(FIXTURE_ROOT / "reference_observations.csv")
    report = compare_csv_rows(
        expected,
        expected[:-1],
        key_columns=("station_id", "timestamp_utc"),
    )
    assert not report.matched
    assert any(item.reason == "missing row" for item in report.differences)


def test_csv_rejects_duplicate_keys() -> None:
    rows = load_csv_rows(FIXTURE_ROOT / "reference_observations.csv")
    with pytest.raises(ValueError, match="Duplicate characterization key"):
        compare_csv_rows(
            rows,
            [rows[0], rows[0]],
            key_columns=("station_id", "timestamp_utc"),
        )
