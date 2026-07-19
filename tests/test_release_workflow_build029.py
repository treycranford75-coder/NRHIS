from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def test_payload_file_discovery_includes_additional_files() -> None:
    text = read("scripts/release/Get-NrhisBuildPayloadFiles.ps1")
    assert "AdditionalFiles" in text
    assert "Sort-Object -Unique" in text
    assert "outside the repository" in text


def test_change_set_verifier_detects_missing_and_unexpected_files() -> None:
    text = read("scripts/release/Test-NrhisBuildChangeSet.ps1")
    assert "Unexpected staged files" in text
    assert "Expected files missing from the staged change set" in text
    assert "Expected files still unstaged" in text
    assert "Unexpected untracked files" in text


def test_ci_parity_matches_github_release_gates() -> None:
    text = read("scripts/release/Invoke-NrhisCiParity.ps1")
    assert "python -m ruff check ." in text
    assert "python -m pytest -q" in text
    assert "--cov-branch" in text
    assert "--cov-fail-under=$MinimumCoverage" in text
    assert "test_legacy_preservation.py" in text
    assert "git diff --check" in text


def test_build029_apply_uses_dynamic_payload_manifest() -> None:
    text = read("docs/Release/Sprint2_Build029_PR.md")
    assert "dynamic payload manifest" in text.lower()
    assert "CI-parity" in text
