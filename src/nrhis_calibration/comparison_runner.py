"""Run characterization comparisons against approved reference cases."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .characterization import (
    CharacterizationDifference,
    NumericTolerance,
    compare_csv_rows,
    compare_json,
    load_csv_rows,
    load_json,
)
from .reference_cases import (
    load_reference_case,
    validate_reference_case,
)


@dataclass(frozen=True)
class ArtifactComparison:
    reference_path: str
    candidate_path: str
    matched: bool
    differences: tuple[CharacterizationDifference, ...]


@dataclass(frozen=True)
class ReferenceComparisonReport:
    case_id: str
    implementation: str
    matched: bool
    artifact_reports: tuple[ArtifactComparison, ...]


class ComparisonRunnerError(ValueError):
    """Raised when a controlled comparison cannot be performed."""


def _candidate_path(candidate_root: Path, reference_path: str) -> Path:
    if reference_path.startswith("artifacts/"):
        reference_path = reference_path.split("/", 1)[1]
    return candidate_root / reference_path


def compare_reference_case(
    manifest_path: str | Path,
    *,
    candidate_root: str | Path,
    require_approved: bool = True,
) -> ReferenceComparisonReport:
    """Compare candidate artifacts against a controlled reference case."""
    manifest = Path(manifest_path).resolve()
    candidate = Path(candidate_root).resolve()

    reference_case = load_reference_case(manifest)
    validate_reference_case(
        reference_case,
        manifest_directory=manifest.parent,
        require_approved=require_approved,
    )

    if not candidate.is_dir():
        raise ComparisonRunnerError(f"Candidate directory is missing: {candidate}")

    artifact_reports: list[ArtifactComparison] = []

    for artifact in reference_case.artifacts:
        reference_path = manifest.parent / artifact.path
        candidate_path = _candidate_path(candidate, artifact.path)

        if not candidate_path.is_file():
            difference = CharacterizationDifference(
                location="$",
                expected=str(reference_path),
                actual=None,
                reason="candidate artifact missing",
            )
            artifact_reports.append(
                ArtifactComparison(
                    reference_path=str(reference_path),
                    candidate_path=str(candidate_path),
                    matched=False,
                    differences=(difference,),
                )
            )
            continue

        suffix = reference_path.suffix.lower()
        if suffix == ".json":
            report = compare_json(
                load_json(reference_path),
                load_json(candidate_path),
                tolerance=NumericTolerance(),
                ignored_keys=reference_case.ignored_json_keys,
            )
        elif suffix == ".csv":
            report = compare_csv_rows(
                load_csv_rows(reference_path),
                load_csv_rows(candidate_path),
                key_columns=reference_case.csv_key_columns,
                numeric_columns=reference_case.numeric_tolerances,
            )
        else:
            expected = reference_path.read_bytes()
            actual = candidate_path.read_bytes()
            differences = ()
            if expected != actual:
                differences = (
                    CharacterizationDifference(
                        location="$",
                        expected=f"{len(expected)} bytes",
                        actual=f"{len(actual)} bytes",
                        reason="binary content mismatch",
                    ),
                )
            report = type(
                "_Report",
                (),
                {"matched": not differences, "differences": differences},
            )()

        artifact_reports.append(
            ArtifactComparison(
                reference_path=str(reference_path),
                candidate_path=str(candidate_path),
                matched=report.matched,
                differences=tuple(report.differences),
            )
        )

    return ReferenceComparisonReport(
        case_id=reference_case.case_id,
        implementation=reference_case.implementation,
        matched=all(report.matched for report in artifact_reports),
        artifact_reports=tuple(artifact_reports),
    )


def write_comparison_report(
    report: ReferenceComparisonReport,
    destination: str | Path,
) -> None:
    path = Path(destination)
    document = {
        "case_id": report.case_id,
        "implementation": report.implementation,
        "matched": report.matched,
        "artifact_reports": [
            {
                "reference_path": item.reference_path,
                "candidate_path": item.candidate_path,
                "matched": item.matched,
                "differences": [asdict(diff) for diff in item.differences],
            }
            for item in report.artifact_reports
        ],
    }
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
