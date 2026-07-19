"""Reference-case manifests and validation for calibration characterization."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .characterization import NumericTolerance, sha256_file


@dataclass(frozen=True)
class ReferenceArtifact:
    path: str
    sha256: str
    media_type: str


@dataclass(frozen=True)
class ReferenceCase:
    case_id: str
    implementation: str
    approved: bool
    description: str
    artifacts: tuple[ReferenceArtifact, ...]
    ignored_json_keys: tuple[str, ...]
    csv_key_columns: tuple[str, ...]
    numeric_tolerances: Mapping[str, NumericTolerance]


class ReferenceCaseError(ValueError):
    """Raised when a reference-case manifest is invalid."""


def _require_string(document: Mapping[str, Any], key: str) -> str:
    value = document.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ReferenceCaseError(f"{key!r} must be a non-empty string")
    return value


def load_reference_case(path: str | Path) -> ReferenceCase:
    manifest_path = Path(path)
    document = json.loads(manifest_path.read_text(encoding="utf-8"))

    if not isinstance(document, dict):
        raise ReferenceCaseError("reference-case manifest must be a JSON object")

    artifacts_raw = document.get("artifacts")
    if not isinstance(artifacts_raw, list) or not artifacts_raw:
        raise ReferenceCaseError("'artifacts' must be a non-empty list")

    artifacts: list[ReferenceArtifact] = []
    for index, item in enumerate(artifacts_raw):
        if not isinstance(item, dict):
            raise ReferenceCaseError(f"artifact {index} must be an object")
        artifact = ReferenceArtifact(
            path=_require_string(item, "path"),
            sha256=_require_string(item, "sha256").upper(),
            media_type=_require_string(item, "media_type"),
        )
        if len(artifact.sha256) != 64:
            raise ReferenceCaseError(f"artifact {index} SHA-256 must be 64 characters")
        artifacts.append(artifact)

    tolerances_raw = document.get("numeric_tolerances", {})
    if not isinstance(tolerances_raw, dict):
        raise ReferenceCaseError("'numeric_tolerances' must be an object")

    tolerances: dict[str, NumericTolerance] = {}
    for column, values in tolerances_raw.items():
        if not isinstance(values, dict):
            raise ReferenceCaseError(f"tolerance for {column!r} must be an object")
        absolute = float(values.get("absolute", 0.0))
        relative = float(values.get("relative", 0.0))
        if absolute < 0 or relative < 0:
            raise ReferenceCaseError("numeric tolerances must be non-negative")
        tolerances[column] = NumericTolerance(absolute=absolute, relative=relative)

    ignored_keys = document.get("ignored_json_keys", [])
    csv_keys = document.get("csv_key_columns", [])
    if not isinstance(ignored_keys, list) or not all(isinstance(v, str) for v in ignored_keys):
        raise ReferenceCaseError("'ignored_json_keys' must be a list of strings")
    if not isinstance(csv_keys, list) or not all(isinstance(v, str) for v in csv_keys):
        raise ReferenceCaseError("'csv_key_columns' must be a list of strings")

    approved = document.get("approved")
    if not isinstance(approved, bool):
        raise ReferenceCaseError("'approved' must be boolean")

    return ReferenceCase(
        case_id=_require_string(document, "case_id"),
        implementation=_require_string(document, "implementation"),
        approved=approved,
        description=_require_string(document, "description"),
        artifacts=tuple(artifacts),
        ignored_json_keys=tuple(ignored_keys),
        csv_key_columns=tuple(csv_keys),
        numeric_tolerances=tolerances,
    )


def validate_reference_case(
    reference_case: ReferenceCase,
    *,
    manifest_directory: str | Path,
    require_approved: bool = False,
) -> tuple[str, ...]:
    if require_approved and not reference_case.approved:
        raise ReferenceCaseError(
            f"reference case {reference_case.case_id!r} is not approved"
        )

    base = Path(manifest_directory)
    verified: list[str] = []

    for artifact in reference_case.artifacts:
        artifact_path = base / artifact.path
        if not artifact_path.is_file():
            raise ReferenceCaseError(f"reference artifact is missing: {artifact.path}")
        actual_hash = sha256_file(artifact_path)
        if actual_hash != artifact.sha256:
            raise ReferenceCaseError(
                f"reference artifact hash mismatch: {artifact.path}"
            )
        verified.append(artifact.path)

    return tuple(verified)


def write_reference_case(
    path: str | Path,
    *,
    case_id: str,
    implementation: str,
    approved: bool,
    description: str,
    artifacts: Sequence[tuple[str | Path, str]],
    ignored_json_keys: Sequence[str] = (),
    csv_key_columns: Sequence[str] = (),
    numeric_tolerances: Mapping[str, NumericTolerance] | None = None,
) -> None:
    destination = Path(path)
    base = destination.parent
    numeric_tolerances = numeric_tolerances or {}

    artifact_documents = []
    for artifact_path, media_type in artifacts:
        artifact_path = Path(artifact_path)
        relative = artifact_path.relative_to(base)
        artifact_documents.append(
            {
                "path": relative.as_posix(),
                "sha256": sha256_file(artifact_path),
                "media_type": media_type,
            }
        )

    document = {
        "case_id": case_id,
        "implementation": implementation,
        "approved": approved,
        "description": description,
        "artifacts": artifact_documents,
        "ignored_json_keys": list(ignored_json_keys),
        "csv_key_columns": list(csv_key_columns),
        "numeric_tolerances": {
            key: {
                "absolute": tolerance.absolute,
                "relative": tolerance.relative,
            }
            for key, tolerance in numeric_tolerances.items()
        },
    }

    destination.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
