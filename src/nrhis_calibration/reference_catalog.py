"""Catalog and discovery utilities for calibration reference cases."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .reference_cases import (
    ReferenceCaseError,
    load_reference_case,
    validate_reference_case,
)


@dataclass(frozen=True)
class ReferenceCatalogEntry:
    case_id: str
    implementation: str
    approved: bool
    description: str
    manifest_path: str
    artifact_count: int
    valid: bool
    validation_error: str | None = None


@dataclass(frozen=True)
class ReferenceCatalog:
    root: str
    entries: tuple[ReferenceCatalogEntry, ...]


def discover_reference_manifests(reference_root: str | Path) -> tuple[Path, ...]:
    root = Path(reference_root).resolve()
    if not root.exists():
        return ()
    return tuple(sorted(root.rglob("case.json")))


def build_reference_catalog(
    reference_root: str | Path,
    *,
    require_approved: bool = False,
) -> ReferenceCatalog:
    root = Path(reference_root).resolve()
    entries: list[ReferenceCatalogEntry] = []

    for manifest in discover_reference_manifests(root):
        try:
            reference_case = load_reference_case(manifest)
            validate_reference_case(
                reference_case,
                manifest_directory=manifest.parent,
                require_approved=require_approved,
            )
        except (ReferenceCaseError, OSError, json.JSONDecodeError, ValueError) as exc:
            entries.append(
                ReferenceCatalogEntry(
                    case_id=manifest.parent.name,
                    implementation="unknown",
                    approved=False,
                    description="Invalid reference case",
                    manifest_path=str(manifest),
                    artifact_count=0,
                    valid=False,
                    validation_error=str(exc),
                )
            )
            continue

        entries.append(
            ReferenceCatalogEntry(
                case_id=reference_case.case_id,
                implementation=reference_case.implementation,
                approved=reference_case.approved,
                description=reference_case.description,
                manifest_path=str(manifest),
                artifact_count=len(reference_case.artifacts),
                valid=True,
                validation_error=None,
            )
        )

    return ReferenceCatalog(root=str(root), entries=tuple(entries))


def filter_catalog(
    catalog: ReferenceCatalog,
    *,
    implementation: str | None = None,
    approved: bool | None = None,
    valid: bool | None = None,
) -> ReferenceCatalog:
    entries = catalog.entries

    if implementation is not None:
        normalized = implementation.strip().lower()
        entries = tuple(
            entry
            for entry in entries
            if entry.implementation.strip().lower() == normalized
        )

    if approved is not None:
        entries = tuple(entry for entry in entries if entry.approved is approved)

    if valid is not None:
        entries = tuple(entry for entry in entries if entry.valid is valid)

    return ReferenceCatalog(root=catalog.root, entries=entries)


def write_catalog_json(
    catalog: ReferenceCatalog,
    destination: str | Path,
) -> None:
    path = Path(destination)
    document = {
        "root": catalog.root,
        "entry_count": len(catalog.entries),
        "entries": [asdict(entry) for entry in catalog.entries],
    }
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
