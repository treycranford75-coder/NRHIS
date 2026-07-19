"""Controlled approval and revocation of calibration reference cases."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .reference_cases import (
    load_reference_case,
    validate_reference_case,
)


class ReferenceApprovalError(ValueError):
    """Raised when a reference case cannot be approved or revoked safely."""


@dataclass(frozen=True)
class ReferenceApprovalRecord:
    case_id: str
    action: str
    reviewer: str
    timestamp_utc: str
    rationale: str
    manifest_path: str
    approval_record_path: str


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_manifest_document(path: Path) -> dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ReferenceApprovalError("reference-case manifest must be a JSON object")
    return document


def _write_manifest_document(path: Path, document: dict[str, object]) -> None:
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def approve_reference_case(
    manifest_path: str | Path,
    *,
    reviewer: str,
    rationale: str,
) -> ReferenceApprovalRecord:
    """Approve a validated reference case and write an immutable review record."""
    manifest = Path(manifest_path).resolve()
    if not reviewer.strip():
        raise ReferenceApprovalError("reviewer must be non-empty")
    if not rationale.strip():
        raise ReferenceApprovalError("rationale must be non-empty")

    reference_case = load_reference_case(manifest)
    validate_reference_case(
        reference_case,
        manifest_directory=manifest.parent,
        require_approved=False,
    )

    if reference_case.approved:
        raise ReferenceApprovalError(
            f"reference case {reference_case.case_id!r} is already approved"
        )

    record_path = manifest.parent / "approval_record.json"
    if record_path.exists():
        raise ReferenceApprovalError(f"approval record already exists: {record_path}")

    timestamp = _timestamp()
    record = {
        "case_id": reference_case.case_id,
        "action": "approve",
        "reviewer": reviewer,
        "timestamp_utc": timestamp,
        "rationale": rationale,
        "manifest_path": str(manifest),
    }
    record_path.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    document = _load_manifest_document(manifest)
    document["approved"] = True
    document["approval_record"] = record_path.name
    _write_manifest_document(manifest, document)

    approved_case = load_reference_case(manifest)
    validate_reference_case(
        approved_case,
        manifest_directory=manifest.parent,
        require_approved=True,
    )

    return ReferenceApprovalRecord(
        case_id=reference_case.case_id,
        action="approve",
        reviewer=reviewer,
        timestamp_utc=timestamp,
        rationale=rationale,
        manifest_path=str(manifest),
        approval_record_path=str(record_path),
    )


def revoke_reference_case(
    manifest_path: str | Path,
    *,
    reviewer: str,
    rationale: str,
) -> ReferenceApprovalRecord:
    """Revoke approval while preserving the original approval record."""
    manifest = Path(manifest_path).resolve()
    if not reviewer.strip():
        raise ReferenceApprovalError("reviewer must be non-empty")
    if not rationale.strip():
        raise ReferenceApprovalError("rationale must be non-empty")

    reference_case = load_reference_case(manifest)
    validate_reference_case(
        reference_case,
        manifest_directory=manifest.parent,
        require_approved=False,
    )

    if not reference_case.approved:
        raise ReferenceApprovalError(f"reference case {reference_case.case_id!r} is not approved")

    revocation_path = manifest.parent / "revocation_record.json"
    if revocation_path.exists():
        raise ReferenceApprovalError(f"revocation record already exists: {revocation_path}")

    timestamp = _timestamp()
    record = {
        "case_id": reference_case.case_id,
        "action": "revoke",
        "reviewer": reviewer,
        "timestamp_utc": timestamp,
        "rationale": rationale,
        "manifest_path": str(manifest),
    }
    revocation_path.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    document = _load_manifest_document(manifest)
    document["approved"] = False
    document["revocation_record"] = revocation_path.name
    _write_manifest_document(manifest, document)

    return ReferenceApprovalRecord(
        case_id=reference_case.case_id,
        action="revoke",
        reviewer=reviewer,
        timestamp_utc=timestamp,
        rationale=rationale,
        manifest_path=str(manifest),
        approval_record_path=str(revocation_path),
    )
