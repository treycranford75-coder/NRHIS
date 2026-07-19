"""Release-evidence bundling for controlled calibration verification."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


class EvidenceBundleError(ValueError):
    """Raised when a release-evidence bundle cannot be created safely."""


@dataclass(frozen=True)
class EvidenceArtifact:
    relative_path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class EvidenceBundle:
    bundle_directory: str
    manifest_path: str
    artifact_count: int
    artifacts: tuple[EvidenceArtifact, ...]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def create_evidence_bundle(
    *,
    destination_root: str | Path,
    bundle_id: str,
    source_artifacts: Iterable[str | Path],
    metadata: dict[str, object],
) -> EvidenceBundle:
    """Copy controlled evidence into an immutable bundle and write a manifest."""
    if not bundle_id.strip():
        raise EvidenceBundleError("bundle_id must be non-empty")

    root = Path(destination_root).resolve()
    bundle_directory = root / bundle_id

    if bundle_directory.exists():
        raise EvidenceBundleError(
            f"Evidence bundle already exists and will not be overwritten: {bundle_directory}"
        )

    artifact_directory = bundle_directory / "artifacts"
    artifact_directory.mkdir(parents=True)

    copied: list[EvidenceArtifact] = []
    seen_names: set[str] = set()

    for source_value in source_artifacts:
        source = Path(source_value).resolve()
        if not source.is_file():
            raise EvidenceBundleError(f"Evidence artifact is missing: {source}")

        name = source.name
        if name in seen_names:
            raise EvidenceBundleError(f"Duplicate evidence filename: {name}")
        seen_names.add(name)

        destination = artifact_directory / name
        shutil.copy2(source, destination)

        copied.append(
            EvidenceArtifact(
                relative_path=destination.relative_to(bundle_directory).as_posix(),
                sha256=_sha256(destination),
                size_bytes=destination.stat().st_size,
            )
        )

    if not copied:
        raise EvidenceBundleError("At least one evidence artifact is required")

    manifest_path = bundle_directory / "evidence_manifest.json"
    document = {
        "bundle_id": bundle_id,
        "metadata": metadata,
        "artifact_count": len(copied),
        "artifacts": [asdict(item) for item in copied],
    }
    manifest_path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return EvidenceBundle(
        bundle_directory=str(bundle_directory),
        manifest_path=str(manifest_path),
        artifact_count=len(copied),
        artifacts=tuple(copied),
    )


def validate_evidence_bundle(manifest_path: str | Path) -> tuple[str, ...]:
    """Validate all evidence artifacts against the bundle manifest."""
    manifest = Path(manifest_path).resolve()
    if not manifest.is_file():
        raise EvidenceBundleError(f"Evidence manifest is missing: {manifest}")

    document = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise EvidenceBundleError("Evidence manifest must be a JSON object")

    artifacts = document.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise EvidenceBundleError("'artifacts' must be a non-empty list")

    verified: list[str] = []
    bundle_directory = manifest.parent

    for index, item in enumerate(artifacts):
        if not isinstance(item, dict):
            raise EvidenceBundleError(f"Artifact {index} must be an object")

        relative_path = item.get("relative_path")
        expected_hash = item.get("sha256")
        expected_size = item.get("size_bytes")

        if not isinstance(relative_path, str) or not relative_path:
            raise EvidenceBundleError(f"Artifact {index} has an invalid path")
        if not isinstance(expected_hash, str) or len(expected_hash) != 64:
            raise EvidenceBundleError(f"Artifact {index} has an invalid SHA-256")
        if not isinstance(expected_size, int) or expected_size < 0:
            raise EvidenceBundleError(f"Artifact {index} has an invalid size")

        artifact_path = bundle_directory / relative_path
        if not artifact_path.is_file():
            raise EvidenceBundleError(f"Evidence artifact is missing: {relative_path}")
        if artifact_path.stat().st_size != expected_size:
            raise EvidenceBundleError(f"Evidence artifact size mismatch: {relative_path}")
        if _sha256(artifact_path) != expected_hash.upper():
            raise EvidenceBundleError(f"Evidence artifact hash mismatch: {relative_path}")

        verified.append(relative_path)

    return tuple(verified)
