import json
from pathlib import Path
import pytest
from nrhis_calibration.archive_retention import (
    ArchiveRetentionError,
    build_retention_plan,
    load_retention_plan,
    summarize_retention_plan,
    write_retention_plan,
)
from nrhis_calibration.sprint_archive_index import SprintArchiveIndex, SprintArchiveIndexEntry

def _index() -> SprintArchiveIndex:
    return SprintArchiveIndex(
        root="archives",
        entries=(
            SprintArchiveIndexEntry("sprint2-old", "old.json", True, 2, {"created_at_utc": "2026-07-17T10:00:00+00:00"}),
            SprintArchiveIndexEntry("sprint2-new", "new.json", True, 2, {"created_at_utc": "2026-07-18T10:00:00+00:00"}),
            SprintArchiveIndexEntry("broken", "broken.json", False, 0, {}, "hash mismatch"),
        ),
    )

def test_retention_plan_classifies_archives() -> None:
    plan = build_retention_plan(_index(), retain_latest=1)
    decisions = {item.archive_id: item.action for item in plan.decisions}
    assert decisions == {
        "sprint2-old": "review",
        "sprint2-new": "retain",
        "broken": "quarantine",
    }
    assert summarize_retention_plan(plan) == {"retain": 1, "review": 1, "quarantine": 1}

def test_retention_plan_rejects_invalid_limit() -> None:
    with pytest.raises(ArchiveRetentionError, match="at least 1"):
        build_retention_plan(_index(), retain_latest=0)

def test_write_and_load_retention_plan(tmp_path: Path) -> None:
    plan = build_retention_plan(_index(), retain_latest=2)
    output = tmp_path / "retention.json"
    write_retention_plan(plan, output)
    document = json.loads(output.read_text(encoding="utf-8"))
    assert document["summary"]["retain"] == 2
    loaded = load_retention_plan(output)
    assert loaded.retain_latest == 2
    assert len(loaded.decisions) == 3
