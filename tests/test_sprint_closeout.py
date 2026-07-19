import json
from pathlib import Path

import pytest

from nrhis_calibration.sprint_closeout import (
    ReleaseRecord,
    SprintCloseoutError,
    evaluate_sprint_closeout,
    load_release_records,
    write_sprint_closeout_report,
)


def _records() -> tuple[ReleaseRecord, ...]:
    return (
        ReleaseRecord(13, "v0.1.1-rc13+build013", "636475f", "Dual-Run Verification", 67, 85.82),
        ReleaseRecord(14, "v0.1.1-rc14+build014", "f9d1492", "Release Evidence Bundles", 73, 85.59),
        ReleaseRecord(15, "v0.1.1-rc15+build015", "eb8bdd1", "Release Acceptance Gate", 78, 85.54),
    )


def test_closeout_accepts_contiguous_release_inventory() -> None:
    report = evaluate_sprint_closeout(
        sprint="Sprint 2",
        records=_records(),
        expected_first_build=13,
        expected_final_build=15,
    )
    assert report.accepted is True
    assert report.release_count == 3


def test_closeout_rejects_missing_build() -> None:
    report = evaluate_sprint_closeout(
        sprint="Sprint 2",
        records=(_records()[0], _records()[2]),
        expected_first_build=13,
        expected_final_build=15,
    )
    assert report.accepted is False
    assert any("continuity failed" in check for check in report.checks)


def test_closeout_rejects_coverage_below_floor() -> None:
    bad = ReleaseRecord(
        15,
        "v0.1.1-rc15+build015",
        "eb8bdd1",
        "Release Acceptance Gate",
        78,
        79.99,
    )
    report = evaluate_sprint_closeout(
        sprint="Sprint 2",
        records=(_records()[0], _records()[1], bad),
        expected_first_build=13,
        expected_final_build=15,
    )
    assert report.accepted is False


def test_load_inventory_and_write_report(tmp_path: Path) -> None:
    inventory = tmp_path / "inventory.json"
    inventory.write_text(
        json.dumps(
            [
                {
                    "build_number": record.build_number,
                    "tag": record.tag,
                    "commit": record.commit,
                    "title": record.title,
                    "test_count": record.test_count,
                    "coverage_percent": record.coverage_percent,
                    "pre_release": record.pre_release,
                }
                for record in _records()
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    records = load_release_records(inventory)
    report = evaluate_sprint_closeout(
        sprint="Sprint 2",
        records=records,
        expected_first_build=13,
        expected_final_build=15,
    )
    output = tmp_path / "closeout.json"
    write_sprint_closeout_report(report, output)
    document = json.loads(output.read_text(encoding="utf-8"))
    assert document["accepted"] is True


def test_load_inventory_rejects_non_array(tmp_path: Path) -> None:
    inventory = tmp_path / "inventory.json"
    inventory.write_text("{}\n", encoding="utf-8")
    with pytest.raises(SprintCloseoutError, match="JSON array"):
        load_release_records(inventory)
