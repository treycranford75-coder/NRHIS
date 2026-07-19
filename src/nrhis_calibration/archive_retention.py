"""Retention-policy controls for immutable Sprint archives."""
from __future__ import annotations
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from .sprint_archive_index import SprintArchiveIndex

class ArchiveRetentionError(ValueError):
    """Raised when an archive retention plan is invalid."""

@dataclass(frozen=True)
class ArchiveRetentionDecision:
    archive_id: str
    manifest_path: str
    action: str
    reason: str

@dataclass(frozen=True)
class ArchiveRetentionPlan:
    generated_at_utc: str
    retain_latest: int
    decisions: tuple[ArchiveRetentionDecision, ...]

def build_retention_plan(index: SprintArchiveIndex, *, retain_latest: int) -> ArchiveRetentionPlan:
    if retain_latest < 1:
        raise ArchiveRetentionError("retain_latest must be at least 1")
    valid_entries = tuple(entry for entry in index.entries if entry.valid)
    ordered_valid = tuple(sorted(
        valid_entries,
        key=lambda entry: (
            str(entry.metadata.get("created_at_utc", "")),
            entry.archive_id,
        ),
        reverse=True,
    ))
    retained_ids = {entry.archive_id for entry in ordered_valid[:retain_latest]}
    decisions = []
    for entry in index.entries:
        if not entry.valid:
            action, reason = "quarantine", "archive validation failed"
        elif entry.archive_id in retained_ids:
            action, reason = "retain", "within latest valid archive set"
        else:
            action, reason = "review", "outside latest valid archive set"
        decisions.append(ArchiveRetentionDecision(
            archive_id=entry.archive_id,
            manifest_path=entry.manifest_path,
            action=action,
            reason=reason,
        ))
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return ArchiveRetentionPlan(generated_at, retain_latest, tuple(decisions))

def summarize_retention_plan(plan: ArchiveRetentionPlan) -> dict[str, int]:
    counts = {"retain": 0, "review": 0, "quarantine": 0}
    for decision in plan.decisions:
        counts[decision.action] = counts.get(decision.action, 0) + 1
    return counts

def write_retention_plan(plan: ArchiveRetentionPlan, destination: str | Path) -> None:
    document = {
        "generated_at_utc": plan.generated_at_utc,
        "retain_latest": plan.retain_latest,
        "summary": summarize_retention_plan(plan),
        "decisions": [asdict(item) for item in plan.decisions],
    }
    Path(destination).write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

def load_retention_plan(path: str | Path) -> ArchiveRetentionPlan:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ArchiveRetentionError("retention plan must be a JSON object")
    raw_decisions = document.get("decisions")
    if not isinstance(raw_decisions, list):
        raise ArchiveRetentionError("'decisions' must be a list")
    decisions = tuple(
        ArchiveRetentionDecision(
            archive_id=str(item["archive_id"]),
            manifest_path=str(item["manifest_path"]),
            action=str(item["action"]),
            reason=str(item["reason"]),
        )
        for item in raw_decisions
    )
    return ArchiveRetentionPlan(
        str(document["generated_at_utc"]),
        int(document["retain_latest"]),
        decisions,
    )
