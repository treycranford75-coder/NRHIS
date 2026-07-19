"""Immutable Sprint closeout archive controls."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path


class SprintArchiveError(ValueError):
    """Raised when a Sprint archive cannot be created or validated."""


@dataclass(frozen=True)
class SprintArchiveArtifact:
    relative_path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class SprintArchive:
    archive_directory: str
    manifest_path: str
    artifacts: tuple[SprintArchiveArtifact, ...]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest().upper()


def create_sprint_archive(
    *,
    destination_root: str | Path,
    archive_id: str,
    release_inventory: str | Path,
    closeout_report: str | Path,
    metadata: dict[str, object],
) -> SprintArchive:
    """Create an immutable archive containing Sprint closeout evidence."""
    if not archive_id.strip():
        raise SprintArchiveError("archive_id must be non-empty")

    inventory = Path(release_inventory).resolve()
    report = Path(closeout_report).resolve()

    if not inventory.is_file():
        raise SprintArchiveError(f"Release inventory is missing: {inventory}")

    if not report.is_file():
        raise SprintArchiveError(f"Closeout report is missing: {report}")

    report_document = json.loads(report.read_text(encoding="utf-8"))

    if report_document.get("accepted") is not True:
        raise SprintArchiveError("Closeout report is not accepted")

    archive_directory = Path(destination_root).resolve() / archive_id

    if archive_directory.exists():
        raise SprintArchiveError(
            f"Sprint archive already exists and will not be overwritten: {archive_directory}"
        )

    artifact_directory = archive_directory / "artifacts"
    artifact_directory.mkdir(parents=True)

    sources = (
        (inventory, "release_inventory.json"),
        (report, "sprint_closeout.json"),
    )

    artifacts: list[SprintArchiveArtifact] = []

    for source, filename in sources:
        destination = artifact_directory / filename
        shutil.copy2(source, destination)

        artifacts.append(
            SprintArchiveArtifact(
                relative_path=destination.relative_to(archive_directory).as_posix(),
                sha256=_sha256(destination),
                size_bytes=destination.stat().st_size,
            )
        )

    manifest_path = archive_directory / "sprint_archive_manifest.json"

    manifest_document = {
        "archive_id": archive_id,
        "metadata": metadata,
        "artifact_count": len(artifacts),
        "artifacts": [asdict(item) for item in artifacts],
    }

    manifest_path.write_text(
        json.dumps(
            manifest_document,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return SprintArchive(
        archive_directory=str(archive_directory),
        manifest_path=str(manifest_path),
        artifacts=tuple(artifacts),
    )


def validate_sprint_archive(
    manifest_path: str | Path,
) -> tuple[str, ...]:
    """Validate all archived Sprint closeout artifacts."""
    manifest = Path(manifest_path).resolve()

    if not manifest.is_file():
        raise SprintArchiveError(f"Sprint archive manifest is missing: {manifest}")

    document = json.loads(manifest.read_text(encoding="utf-8"))

    artifacts = document.get("artifacts")

    if not isinstance(artifacts, list) or not artifacts:
        raise SprintArchiveError("'artifacts' must be a non-empty list")

    verified: list[str] = []

    for index, item in enumerate(artifacts):
        if not isinstance(item, dict):
            raise SprintArchiveError(f"Artifact {index} must be an object")

        relative_path = item.get("relative_path")
        expected_hash = item.get("sha256")
        expected_size = item.get("size_bytes")

        if not isinstance(relative_path, str) or not relative_path:
            raise SprintArchiveError(f"Artifact {index} has an invalid path")

        if not isinstance(expected_hash, str) or len(expected_hash) != 64:
            raise SprintArchiveError(f"Artifact {index} has an invalid SHA-256")

        if not isinstance(expected_size, int) or expected_size < 0:
            raise SprintArchiveError(f"Artifact {index} has an invalid size")

        artifact = manifest.parent / relative_path

        if not artifact.is_file():
            raise SprintArchiveError(f"Sprint archive artifact is missing: {relative_path}")

        if artifact.stat().st_size != expected_size:
            raise SprintArchiveError(f"Sprint archive artifact size mismatch: {relative_path}")

        if _sha256(artifact) != expected_hash.upper():
            raise SprintArchiveError(f"Sprint archive artifact hash mismatch: {relative_path}")

        verified.append(relative_path)

    required = {
        "artifacts/release_inventory.json",
        "artifacts/sprint_closeout.json",
    }

    if set(verified) != required:
        raise SprintArchiveError(f"Sprint archive contents differ from required set: {verified}")

    return tuple(sorted(verified))
