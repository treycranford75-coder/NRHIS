"""Approval controls for Sprint archive retention plans."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .archive_retention import load_retention_plan


class ArchiveRetentionApprovalError(ValueError):
    """Raised when a retention approval record is invalid."""


@dataclass(frozen=True)
class ArchiveRetentionApproval:
    plan_sha256: str
    approved_at_utc: str
    reviewer: str
    rationale: str
    approved_actions: tuple[str, ...]
    decision_count: int


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def approve_retention_plan(
    *,
    plan_path: str | Path,
    reviewer: str,
    rationale: str,
    approved_actions: tuple[str, ...] = ("retain", "review", "quarantine"),
) -> ArchiveRetentionApproval:
    plan_file = Path(plan_path).resolve()

    if not plan_file.is_file():
        raise ArchiveRetentionApprovalError(
            f"Retention plan is missing: {plan_file}"
        )
    if not reviewer.strip():
        raise ArchiveRetentionApprovalError("reviewer must be non-empty")
    if not rationale.strip():
        raise ArchiveRetentionApprovalError("rationale must be non-empty")

    allowed = {"retain", "review", "quarantine"}
    selected = tuple(dict.fromkeys(approved_actions))

    if not selected:
        raise ArchiveRetentionApprovalError(
            "At least one approved action is required"
        )

    invalid = sorted(set(selected) - allowed)
    if invalid:
        raise ArchiveRetentionApprovalError(
            f"Unsupported approved action(s): {invalid}"
        )

    plan = load_retention_plan(plan_file)
    unapproved = sorted(
        {
            decision.action
            for decision in plan.decisions
            if decision.action not in selected
        }
    )
    if unapproved:
        raise ArchiveRetentionApprovalError(
            f"Plan contains unapproved action(s): {unapproved}"
        )

    approved_at = datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat()

    return ArchiveRetentionApproval(
        plan_sha256=_sha256(plan_file),
        approved_at_utc=approved_at,
        reviewer=reviewer.strip(),
        rationale=rationale.strip(),
        approved_actions=selected,
        decision_count=len(plan.decisions),
    )


def write_retention_approval(
    approval: ArchiveRetentionApproval,
    destination: str | Path,
) -> None:
    Path(destination).write_text(
        json.dumps(asdict(approval), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def validate_retention_approval(
    *,
    plan_path: str | Path,
    approval_path: str | Path,
) -> ArchiveRetentionApproval:
    plan_file = Path(plan_path).resolve()
    approval_file = Path(approval_path).resolve()

    if not plan_file.is_file():
        raise ArchiveRetentionApprovalError(
            f"Retention plan is missing: {plan_file}"
        )
    if not approval_file.is_file():
        raise ArchiveRetentionApprovalError(
            f"Retention approval is missing: {approval_file}"
        )

    document = json.loads(approval_file.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ArchiveRetentionApprovalError(
            "Retention approval must be a JSON object"
        )

    approval = ArchiveRetentionApproval(
        plan_sha256=str(document["plan_sha256"]),
        approved_at_utc=str(document["approved_at_utc"]),
        reviewer=str(document["reviewer"]),
        rationale=str(document["rationale"]),
        approved_actions=tuple(document["approved_actions"]),
        decision_count=int(document["decision_count"]),
    )

    if approval.plan_sha256.upper() != _sha256(plan_file):
        raise ArchiveRetentionApprovalError(
            "Retention plan hash does not match approval"
        )

    plan = load_retention_plan(plan_file)
    if approval.decision_count != len(plan.decisions):
        raise ArchiveRetentionApprovalError(
            "Retention plan decision count does not match approval"
        )

    return approval
