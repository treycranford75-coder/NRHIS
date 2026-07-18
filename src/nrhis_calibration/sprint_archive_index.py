"""Index immutable Sprint archives for discovery and audit."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .sprint_archive import SprintArchiveError, validate_sprint_archive


@dataclass(frozen=True)
class SprintArchiveIndexEntry:
    archive_id: str
    manifest_path: str
    valid: bool
    artifact_count: int
    metadata: dict[str, object]
    validation_error: str | None = None


@dataclass(frozen=True)
class SprintArchiveIndex:
    root: str
    entries: tuple[SprintArchiveIndexEntry, ...]


def discover_sprint_archive_manifests(
    archive_root: str | Path,
) -> tuple[Path, ...]:
    root = Path(archive_root).resolve()
    if not root.exists():
        return ()
    return tuple(sorted(root.rglob("sprint_archive_manifest.json")))


def build_sprint_archive_index(
    archive_root: str | Path,
) -> SprintArchiveIndex:
    root = Path(archive_root).resolve()
    entries: list[SprintArchiveIndexEntry] = []

    for manifest in discover_sprint_archive_manifests(root):
        try:
            verified = validate_sprint_archive(manifest)
            document = json.loads(manifest.read_text(encoding="utf-8"))
            archive_id = str(document.get("archive_id", manifest.parent.name))
            metadata = document.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}
            entries.append(
                SprintArchiveIndexEntry(
                    archive_id=archive_id,
                    manifest_path=str(manifest),
                    valid=True,
                    artifact_count=len(verified),
                    metadata=metadata,
                )
            )
        except (SprintArchiveError, OSError, json.JSONDecodeError, ValueError) as exc:
            entries.append(
                SprintArchiveIndexEntry(
                    archive_id=manifest.parent.name,
                    manifest_path=str(manifest),
                    valid=False,
                    artifact_count=0,
                    metadata={},
                    validation_error=str(exc),
                )
            )

    return SprintArchiveIndex(root=str(root), entries=tuple(entries))


def filter_sprint_archive_index(
    index: SprintArchiveIndex,
    *,
    valid: bool | None = None,
    sprint: str | None = None,
) -> SprintArchiveIndex:
    entries = index.entries

    if valid is not None:
        entries = tuple(entry for entry in entries if entry.valid is valid)

    if sprint is not None:
        normalized = sprint.strip().lower()
        entries = tuple(
            entry
            for entry in entries
            if str(entry.metadata.get("sprint", "")).strip().lower() == normalized
        )

    return SprintArchiveIndex(root=index.root, entries=entries)


def write_sprint_archive_index(
    index: SprintArchiveIndex,
    destination: str | Path,
) -> None:
    path = Path(destination)
    document = {
        "root": index.root,
        "archive_count": len(index.entries),
        "entries": [asdict(entry) for entry in index.entries],
    }
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
