"""Sprint closeout manifest and release-inventory controls."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


class SprintCloseoutError(ValueError):
    """Raised when a sprint closeout record is incomplete or invalid."""


@dataclass(frozen=True)
class ReleaseRecord:
    build_number: int
    tag: str
    commit: str
    title: str
    test_count: int
    coverage_percent: float
    pre_release: bool = True


@dataclass(frozen=True)
class SprintCloseoutReport:
    sprint: str
    accepted: bool
    release_count: int
    first_build: int
    final_build: int
    records: tuple[ReleaseRecord, ...]
    checks: tuple[str, ...]


def _validate_record(record: ReleaseRecord) -> None:
    if record.build_number < 1:
        raise SprintCloseoutError("build_number must be positive")
    if not record.tag.strip():
        raise SprintCloseoutError("tag must be non-empty")
    if not record.commit.strip():
        raise SprintCloseoutError("commit must be non-empty")
    if not record.title.strip():
        raise SprintCloseoutError("title must be non-empty")
    if record.test_count < 0:
        raise SprintCloseoutError("test_count must be non-negative")
    if not 0.0 <= record.coverage_percent <= 100.0:
        raise SprintCloseoutError("coverage_percent must be between 0 and 100")


def evaluate_sprint_closeout(
    *,
    sprint: str,
    records: Iterable[ReleaseRecord],
    expected_first_build: int,
    expected_final_build: int,
    minimum_coverage_percent: float = 80.0,
) -> SprintCloseoutReport:
    if not sprint.strip():
        raise SprintCloseoutError("sprint must be non-empty")
    if expected_first_build < 1:
        raise SprintCloseoutError("expected_first_build must be positive")
    if expected_final_build < expected_first_build:
        raise SprintCloseoutError(
            "expected_final_build must be greater than or equal to expected_first_build"
        )

    ordered = tuple(sorted(records, key=lambda item: item.build_number))
    for record in ordered:
        _validate_record(record)

    checks: list[str] = []
    expected_numbers = tuple(range(expected_first_build, expected_final_build + 1))
    actual_numbers = tuple(record.build_number for record in ordered)

    continuity_ok = actual_numbers == expected_numbers
    checks.append(
        "build continuity verified"
        if continuity_ok
        else f"build continuity failed: expected {expected_numbers}, got {actual_numbers}"
    )

    unique_tags = len({record.tag for record in ordered}) == len(ordered)
    checks.append("release tags unique" if unique_tags else "duplicate release tag detected")

    unique_commits = len({record.commit for record in ordered}) == len(ordered)
    checks.append(
        "release commits unique" if unique_commits else "duplicate release commit detected"
    )

    coverage_ok = all(record.coverage_percent >= minimum_coverage_percent for record in ordered)
    checks.append(
        f"coverage floor {minimum_coverage_percent:.2f}% satisfied"
        if coverage_ok
        else f"coverage floor {minimum_coverage_percent:.2f}% failed"
    )

    tests_ok = all(record.test_count > 0 for record in ordered)
    checks.append("test evidence present" if tests_ok else "missing test evidence")

    prerelease_ok = all(record.pre_release for record in ordered)
    checks.append(
        "all releases marked pre-release"
        if prerelease_ok
        else "one or more releases are not marked pre-release"
    )

    accepted = all(
        (continuity_ok, unique_tags, unique_commits, coverage_ok, tests_ok, prerelease_ok)
    )

    return SprintCloseoutReport(
        sprint=sprint,
        accepted=accepted,
        release_count=len(ordered),
        first_build=expected_first_build,
        final_build=expected_final_build,
        records=ordered,
        checks=tuple(checks),
    )


def write_sprint_closeout_report(
    report: SprintCloseoutReport,
    destination: str | Path,
) -> None:
    path = Path(destination)
    document = {
        "sprint": report.sprint,
        "accepted": report.accepted,
        "release_count": report.release_count,
        "first_build": report.first_build,
        "final_build": report.final_build,
        "checks": list(report.checks),
        "records": [asdict(record) for record in report.records],
    }
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_release_records(path: str | Path) -> tuple[ReleaseRecord, ...]:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(document, list):
        raise SprintCloseoutError("release inventory must be a JSON array")

    records: list[ReleaseRecord] = []
    for index, item in enumerate(document):
        if not isinstance(item, dict):
            raise SprintCloseoutError(f"release record {index} must be an object")
        try:
            record = ReleaseRecord(
                build_number=int(item["build_number"]),
                tag=str(item["tag"]),
                commit=str(item["commit"]),
                title=str(item["title"]),
                test_count=int(item["test_count"]),
                coverage_percent=float(item["coverage_percent"]),
                pre_release=bool(item.get("pre_release", True)),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SprintCloseoutError(f"release record {index} is malformed") from exc
        _validate_record(record)
        records.append(record)

    return tuple(records)
