"""Cross-platform integrity tests for tracked legacy Pass1 files."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LEGACY_ROOT = REPOSITORY_ROOT / "src" / "nrhis_calibration" / "legacy"
MANIFEST_PATH = LEGACY_ROOT / "SHA256SUMS.txt"

TEXT_SUFFIXES = {
    ".bat",
    ".csv",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}


def _normalized_relative_path(path_text: str) -> Path:
    return Path(*path_text.replace("\\", "/").split("/"))


def _canonical_bytes(path: Path) -> bytes:
    data = path.read_bytes()

    if path.suffix.lower() in TEXT_SUFFIXES:
        data = data.replace(b"\r\n", b"\n")

    return data


def _sha256(path: Path) -> str:
    return hashlib.sha256(_canonical_bytes(path)).hexdigest().upper()


def _tracked_legacy_paths() -> set[Path]:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--",
            "src/nrhis_calibration/legacy",
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    return {
        _normalized_relative_path(line.strip())
        for line in result.stdout.splitlines()
        if line.strip()
        and _normalized_relative_path(line.strip()) != MANIFEST_PATH.relative_to(REPOSITORY_ROOT)
    }


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
        assert relative_path not in entries, f"Duplicate manifest entry: {relative_path}"
        entries[relative_path] = expected_hash.upper()

    return entries


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


def test_manifest_matches_tracked_legacy_tree() -> None:
    manifest_paths = set(_load_manifest())
    tracked_paths = _tracked_legacy_paths()

    missing_from_repository = manifest_paths - tracked_paths
    missing_from_manifest = tracked_paths - manifest_paths

    assert not missing_from_repository, "Manifest contains files not tracked by Git: " + ", ".join(
        str(path) for path in sorted(missing_from_repository)
    )
    assert not missing_from_manifest, (
        "Tracked legacy files are missing from the manifest: "
        + ", ".join(str(path) for path in sorted(missing_from_manifest))
    )
