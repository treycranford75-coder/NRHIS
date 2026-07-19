"""Generate controlled, non-destructive archive retention action manifests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .archive_retention import load_retention_plan
from .archive_retention_approval import validate_retention_approval


class ArchiveRetentionActionError(ValueError):
    """Raised when an action manifest cannot be generated or validated."""


@dataclass(frozen=True)
class ArchiveRetentionAction:
    archive_id: str
    manifest_path: str
    requested_action: str
    executable: bool
    reason: str


@dataclass(frozen=True)
class ArchiveRetentionActionManifest:
    plan_sha256: str
    approval_sha256: str
    dry_run: bool
    actions: tuple[ArchiveRetentionAction, ...]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def build_action_manifest(
    *,
    plan_path: str | Path,
    approval_path: str | Path,
    dry_run: bool = True,
) -> ArchiveRetentionActionManifest:
    """Build a reviewed action manifest without changing archive files."""
    plan_file = Path(plan_path).resolve()
    approval_file = Path(approval_path).resolve()

    approval = validate_retention_approval(
        plan_path=plan_file,
        approval_path=approval_file,
    )
    plan = load_retention_plan(plan_file)

    actions: list[ArchiveRetentionAction] = []
    for decision in plan.decisions:
        if decision.action not in approval.approved_actions:
            raise ArchiveRetentionActionError(
                f"Action is not approved: {decision.action}"
            )

        executable = decision.action in {"retain", "review", "quarantine"}
        actions.append(
            ArchiveRetentionAction(
                archive_id=decision.archive_id,
                manifest_path=decision.manifest_path,
                requested_action=decision.action,
                executable=executable,
                reason=decision.reason,
            )
        )

    return ArchiveRetentionActionManifest(
        plan_sha256=_sha256(plan_file),
        approval_sha256=_sha256(approval_file),
        dry_run=dry_run,
        actions=tuple(actions),
    )


def write_action_manifest(
    manifest: ArchiveRetentionActionManifest,
    destination: str | Path,
) -> None:
    """Write a deterministic action manifest."""
    document = {
        "plan_sha256": manifest.plan_sha256,
        "approval_sha256": manifest.approval_sha256,
        "dry_run": manifest.dry_run,
        "action_count": len(manifest.actions),
        "actions": [asdict(action) for action in manifest.actions],
    }
    Path(destination).write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def validate_action_manifest(
    *,
    plan_path: str | Path,
    approval_path: str | Path,
    action_manifest_path: str | Path,
) -> ArchiveRetentionActionManifest:
    """Validate an action manifest against its plan and approval."""
    plan_file = Path(plan_path).resolve()
    approval_file = Path(approval_path).resolve()
    manifest_file = Path(action_manifest_path).resolve()

    if not manifest_file.is_file():
        raise ArchiveRetentionActionError(
            f"Action manifest is missing: {manifest_file}"
        )

    document = json.loads(manifest_file.read_text(encoding="utf-8"))
    if document.get("plan_sha256", "").upper() != _sha256(plan_file):
        raise ArchiveRetentionActionError("Plan hash mismatch")
    if document.get("approval_sha256", "").upper() != _sha256(approval_file):
        raise ArchiveRetentionActionError("Approval hash mismatch")

    regenerated = build_action_manifest(
        plan_path=plan_file,
        approval_path=approval_file,
        dry_run=bool(document.get("dry_run", True)),
    )

    if int(document.get("action_count", -1)) != len(regenerated.actions):
        raise ArchiveRetentionActionError("Action count mismatch")

    return regenerated
