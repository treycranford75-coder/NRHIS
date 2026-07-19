from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8-sig")


def test_validation_script_contains_required_gates() -> None:
    text = _read("scripts/release/Invoke-NrhisReleaseValidation.ps1")

    assert "python -m pytest -q" in text
    assert "python -m ruff check ." in text
    assert "--cov-fail-under=$MinimumCoverage" in text
    assert "test_legacy_preservation.py" in text
    assert "git diff --check" in text


def test_pull_request_script_does_not_merge() -> None:
    text = _read("scripts/release/New-NrhisPullRequest.ps1")

    assert "gh pr create" in text
    assert "gh pr merge" not in text
    assert "compare/${BaseBranch}...${HeadBranch}?expand=1" in text


def test_release_completion_requires_clean_tree_and_publishes_prerelease() -> None:
    text = _read("scripts/release/Complete-NrhisRelease.ps1")

    assert "git status --porcelain" in text
    assert "Working tree is not clean" in text
    assert "git tag -a $Tag" in text
    assert "git push origin $Tag" in text
    assert "gh release create $Tag" in text
    assert "--prerelease" in text
    assert "gh pr merge" not in text
