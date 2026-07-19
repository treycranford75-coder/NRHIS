"""Simulate controlled execution of archive-retention action manifests."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .archive_retention_action import validate_action_manifest


class ArchiveRetentionExecutionError(ValueError):
    """Raised when a retention execution simulation is invalid."""


@dataclass(frozen=True)
class ArchiveRetentionExecutionItem:
    archive_id: str
    requested_action: str
    status: str
    message: str


@dataclass(frozen=True)
class ArchiveRetentionExecutionReport:
    dry_run: bool
    executed: bool
    item_count: int
    items: tuple[ArchiveRetentionExecutionItem, ...]


def simulate_retention_execution(
    *,
    plan_path: str | Path,
    approval_path: str | Path,
    action_manifest_path: str | Path,
) -> ArchiveRetentionExecutionReport:
    """Simulate retention execution without changing archive files."""
    manifest = validate_action_manifest(
        plan_path=plan_path,
        approval_path=approval_path,
        action_manifest_path=action_manifest_path,
    )

    if not manifest.dry_run:
        raise ArchiveRetentionExecutionError(
            "Build022 accepts dry-run action manifests only"
        )

    items: list[ArchiveRetentionExecutionItem] = []
    for action in manifest.actions:
        if action.requested_action == "retain":
            status = "simulated-retain"
            message = "Archive would remain in place."
        elif action.requested_action == "review":
            status = "simulated-review"
            message = "Archive would remain pending manual review."
        elif action.requested_action == "quarantine":
            status = "simulated-quarantine"
            message = "Archive would be proposed for quarantine."
        else:
            raise ArchiveRetentionExecutionError(
                f"Unsupported requested action: {action.requested_action}"
            )

        items.append(
            ArchiveRetentionExecutionItem(
                archive_id=action.archive_id,
                requested_action=action.requested_action,
                status=status,
                message=message,
            )
        )

    return ArchiveRetentionExecutionReport(
        dry_run=True,
        executed=False,
        item_count=len(items),
        items=tuple(items),
    )


def write_execution_report(
    report: ArchiveRetentionExecutionReport,
    destination: str | Path,
) -> None:
    """Write a deterministic simulation report."""
    document = {
        "dry_run": report.dry_run,
        "executed": report.executed,
        "item_count": report.item_count,
        "items": [asdict(item) for item in report.items],
    }
    Path(destination).write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def validate_execution_report(
    report_path: str | Path,
) -> ArchiveRetentionExecutionReport:
    """Validate that a report is a non-executing dry-run record."""
    document = json.loads(Path(report_path).read_text(encoding="utf-8"))

    if document.get("dry_run") is not True:
        raise ArchiveRetentionExecutionError(
            "Execution report must be a dry run"
        )
    if document.get("executed") is not False:
        raise ArchiveRetentionExecutionError(
            "Execution report must not indicate live execution"
        )

    raw_items = document.get("items")
    if not isinstance(raw_items, list):
        raise ArchiveRetentionExecutionError("'items' must be a list")

    items = tuple(
        ArchiveRetentionExecutionItem(
            archive_id=str(item["archive_id"]),
            requested_action=str(item["requested_action"]),
            status=str(item["status"]),
            message=str(item["message"]),
        )
        for item in raw_items
    )

    if int(document.get("item_count", -1)) != len(items):
        raise ArchiveRetentionExecutionError(
            "Execution item count mismatch"
        )

    return ArchiveRetentionExecutionReport(
        dry_run=True,
        executed=False,
        item_count=len(items),
        items=items,
    )
