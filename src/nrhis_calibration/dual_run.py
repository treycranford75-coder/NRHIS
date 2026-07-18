"""Dual-run orchestration for controlled calibration verification."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .api import CalibrationRunRequest, CalibrationRunResult, run_calibration
from .comparison_runner import (
    ReferenceComparisonReport,
    compare_reference_case,
    write_comparison_report,
)


class DualRunError(ValueError):
    """Raised when a dual-run verification cannot be completed."""


@dataclass(frozen=True)
class DualRunResult:
    case_id: str
    implementation: str
    run_result: CalibrationRunResult
    comparison_report: ReferenceComparisonReport
    matched: bool
    comparison_report_path: str


def run_dual_verification(
    *,
    manifest_path: str | Path,
    output_root: str | Path,
    implementation: str = "legacy-pass1",
    extra_args: tuple[str, ...] = (),
    timeout_seconds: float | None = None,
    dry_run: bool = False,
    require_approved: bool = True,
) -> DualRunResult:
    """Run calibration and compare its artifacts to a controlled reference case."""
    output_root_path = Path(output_root).resolve()
    output_root_path.mkdir(parents=True, exist_ok=True)

    run_result = run_calibration(
        CalibrationRunRequest(
            output_root=output_root_path,
            implementation=implementation,
            extra_args=extra_args,
            timeout_seconds=timeout_seconds,
            dry_run=dry_run,
        )
    )

    if not run_result.succeeded or run_result.return_code != 0:
        raise DualRunError(
            f"Calibration run failed with return code {run_result.return_code}"
        )

    candidate_root = Path(run_result.metadata_path).resolve().parent
    comparison_report = compare_reference_case(
        manifest_path,
        candidate_root=candidate_root,
        require_approved=require_approved,
    )

    comparison_report_path = candidate_root / "comparison_report.json"
    write_comparison_report(comparison_report, comparison_report_path)

    return DualRunResult(
        case_id=comparison_report.case_id,
        implementation=implementation,
        run_result=run_result,
        comparison_report=comparison_report,
        matched=comparison_report.matched,
        comparison_report_path=str(comparison_report_path),
    )


def write_dual_run_summary(
    result: DualRunResult,
    destination: str | Path,
) -> None:
    """Write a deterministic JSON summary of the dual-run verification."""
    path = Path(destination)
    document = {
        "case_id": result.case_id,
        "implementation": result.implementation,
        "matched": result.matched,
        "comparison_report_path": result.comparison_report_path,
        "run_result": asdict(result.run_result),
    }
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
