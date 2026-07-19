"""Controlled capture of calibration run artifacts into reference cases."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from .characterization import NumericTolerance
from .reference_cases import write_reference_case


class ReferenceCaptureError(ValueError):
    """Raised when a calibration run cannot be captured safely."""


@dataclass(frozen=True)
class CapturedReferenceCase:
    case_directory: str
    manifest_path: str
    artifact_paths: tuple[str, ...]


def _utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _load_run_metadata(run_directory: Path) -> dict[str, object]:
    metadata_path = run_directory / "metadata.json"
    if not metadata_path.is_file():
        raise ReferenceCaptureError(f"Run metadata is missing: {metadata_path}")

    document = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ReferenceCaptureError("Run metadata must be a JSON object")
    return document


def capture_reference_case(
    *,
    run_directory: str | Path,
    reference_root: str | Path,
    case_id: str,
    description: str,
    implementation: str = "legacy-pass1",
    artifact_names: Iterable[str] = ("metadata.json", "stdout.log", "stderr.log"),
    ignored_json_keys: Iterable[str] = (
        "run_id",
        "started_at_utc",
        "finished_at_utc",
        "duration_seconds",
        "stdout_path",
        "stderr_path",
        "metadata_path",
    ),
    numeric_tolerances: dict[str, NumericTolerance] | None = None,
) -> CapturedReferenceCase:
    """Capture one run into an immutable, unapproved reference-case directory."""
    source = Path(run_directory).resolve()
    destination_root = Path(reference_root).resolve()

    if not source.is_dir():
        raise ReferenceCaptureError(f"Run directory is missing: {source}")
    if not case_id.strip():
        raise ReferenceCaptureError("case_id must be non-empty")
    if not description.strip():
        raise ReferenceCaptureError("description must be non-empty")

    metadata = _load_run_metadata(source)
    return_code = metadata.get("return_code")
    succeeded = metadata.get("succeeded")

    if return_code != 0 or succeeded is not True:
        raise ReferenceCaptureError(
            "Only successful calibration runs may be captured as reference cases"
        )

    destination = destination_root / case_id
    if destination.exists():
        raise ReferenceCaptureError(
            f"Reference case already exists and will not be overwritten: {destination}"
        )

    artifact_directory = destination / "artifacts"
    artifact_directory.mkdir(parents=True)

    copied: list[Path] = []
    for name in artifact_names:
        source_path = source / name
        if not source_path.is_file():
            raise ReferenceCaptureError(f"Required run artifact is missing: {source_path}")

        destination_path = artifact_directory / name
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
        copied.append(destination_path)

    capture_record = {
        "case_id": case_id,
        "captured_at_utc": _utc_timestamp(),
        "source_run_directory": str(source),
        "source_run_id": metadata.get("run_id"),
        "implementation": implementation,
        "approved": False,
        "note": "Capture is unapproved until separately reviewed and promoted.",
    }
    capture_record_path = destination / "capture_record.json"
    capture_record_path.write_text(
        json.dumps(capture_record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    copied.append(capture_record_path)

    manifest_path = destination / "case.json"
    write_reference_case(
        manifest_path,
        case_id=case_id,
        implementation=implementation,
        approved=False,
        description=description,
        artifacts=[
            (
                path,
                "application/json" if path.suffix.lower() == ".json" else "text/plain",
            )
            for path in copied
        ],
        ignored_json_keys=tuple(ignored_json_keys),
        numeric_tolerances=numeric_tolerances,
    )

    return CapturedReferenceCase(
        case_directory=str(destination),
        manifest_path=str(manifest_path),
        artifact_paths=tuple(str(path) for path in copied),
    )
