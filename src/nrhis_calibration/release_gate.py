"""Release acceptance gate for calibration verification evidence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .evidence_bundle import EvidenceBundleError, validate_evidence_bundle


class ReleaseGateError(ValueError):
    """Raised when release evidence cannot be evaluated."""


@dataclass(frozen=True)
class ReleaseGateCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class ReleaseGateReport:
    release_id: str
    accepted: bool
    evidence_manifest: str
    checks: tuple[ReleaseGateCheck, ...]


def evaluate_release_gate(
    *,
    release_id: str,
    evidence_manifest: str | Path,
    require_matched_comparison: bool = True,
) -> ReleaseGateReport:
    """Evaluate release evidence and return a deterministic acceptance report."""
    if not release_id.strip():
        raise ReleaseGateError("release_id must be non-empty")

    manifest = Path(evidence_manifest).resolve()
    checks: list[ReleaseGateCheck] = []

    try:
        verified = validate_evidence_bundle(manifest)
    except EvidenceBundleError as exc:
        checks.append(
            ReleaseGateCheck(
                name="evidence_bundle_integrity",
                passed=False,
                detail=str(exc),
            )
        )
        return ReleaseGateReport(
            release_id=release_id,
            accepted=False,
            evidence_manifest=str(manifest),
            checks=tuple(checks),
        )

    checks.append(
        ReleaseGateCheck(
            name="evidence_bundle_integrity",
            passed=True,
            detail=f"{len(verified)} artifacts verified",
        )
    )

    document = json.loads(manifest.read_text(encoding="utf-8"))
    artifact_entries = document.get("artifacts", [])
    artifact_paths = {
        Path(item["relative_path"]).name: manifest.parent / item["relative_path"]
        for item in artifact_entries
        if isinstance(item, dict) and isinstance(item.get("relative_path"), str)
    }

    required_names = {
        "dual_run_summary.json",
        "comparison_report.json",
    }

    for name in sorted(required_names):
        path = artifact_paths.get(name)
        checks.append(
            ReleaseGateCheck(
                name=f"required_artifact:{name}",
                passed=path is not None and path.is_file(),
                detail=str(path) if path is not None else "missing",
            )
        )

    comparison_path = artifact_paths.get("comparison_report.json")
    if require_matched_comparison and comparison_path and comparison_path.is_file():
        comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
        matched = comparison.get("matched") is True
        checks.append(
            ReleaseGateCheck(
                name="comparison_matched",
                passed=matched,
                detail=f"matched={comparison.get('matched')!r}",
            )
        )
    elif require_matched_comparison:
        checks.append(
            ReleaseGateCheck(
                name="comparison_matched",
                passed=False,
                detail="comparison report unavailable",
            )
        )

    accepted = all(check.passed for check in checks)
    return ReleaseGateReport(
        release_id=release_id,
        accepted=accepted,
        evidence_manifest=str(manifest),
        checks=tuple(checks),
    )


def write_release_gate_report(
    report: ReleaseGateReport,
    destination: str | Path,
) -> None:
    """Write the release-gate report as deterministic JSON."""
    path = Path(destination)
    document = {
        "release_id": report.release_id,
        "accepted": report.accepted,
        "evidence_manifest": report.evidence_manifest,
        "checks": [asdict(check) for check in report.checks],
    }
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
