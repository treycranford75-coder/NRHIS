"""Integrity tests for the preserved legacy Pass1 calibration tree."""

from __future__ import annotations

import hashlib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LEGACY_ROOT = REPOSITORY_ROOT / "src" / "nrhis_calibration" / "legacy"
MANIFEST_PATH = LEGACY_ROOT / "SHA256SUMS.txt"


def _normalized_relative_path(path_text: str) -> Path:
    """Convert manifest paths written on Windows or POSIX to a local Path."""
    return Path(*path_text.replace("\\", "/").split("/"))


def _load_manifest() -> dict[Path, str]:
    entries: dict[Path, str] = {}

    for line_number, raw_line in enumerate(
        MANIFEST_PATH.read_text(encoding="utf-8-sig").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line:
            continue

        try:
            expected_hash, path_text = line.split(maxsplit=1)
        except ValueError as exc:
            raise AssertionError(
                f"Invalid SHA256 manifest entry on line {line_number}: {raw_line!r}"
            ) from exc

        relative_path = _normalized_relative_path(path_text.strip())
        assert relative_path not in entries, (
            f"Duplicate manifest entry: {relative_path}"
        )
        entries[relative_path] = expected_hash.upper()

    return entries


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest().upper()


def test_legacy_manifest_exists_and_is_not_empty() -> None:
    assert LEGACY_ROOT.is_dir(), f"Legacy directory missing: {LEGACY_ROOT}"
    assert MANIFEST_PATH.is_file(), f"Legacy manifest missing: {MANIFEST_PATH}"
    assert _load_manifest(), "Legacy preservation manifest is empty"


def test_all_manifested_legacy_files_exist_and_match_sha256() -> None:
    manifest = _load_manifest()

    for relative_path, expected_hash in sorted(
        manifest.items(),
        key=lambda item: str(item[0]),
    ):
        file_path = REPOSITORY_ROOT / relative_path

        assert file_path.is_file(), f"Preserved legacy file missing: {relative_path}"
        assert _sha256(file_path) == expected_hash, (
            f"Preserved legacy file changed: {relative_path}"
        )


def test_legacy_tree_contains_no_unmanifested_files() -> None:
    manifest_paths = set(_load_manifest())

    actual_paths = {
        path.relative_to(REPOSITORY_ROOT)
        for path in LEGACY_ROOT.rglob("*")
        if path.is_file() and path != MANIFEST_PATH
    }

    missing_from_tree = manifest_paths - actual_paths
    unmanifested_files = actual_paths - manifest_paths

    assert not missing_from_tree, (
        "Files listed in the legacy manifest are missing: "
        + ", ".join(str(path) for path in sorted(missing_from_tree))
    )
    assert not unmanifested_files, (
        "Unmanifested files were added to the preserved legacy tree: "
        + ", ".join(str(path) for path in sorted(unmanifested_files))
    )
