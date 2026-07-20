from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_finish_uses_empty_result_safe_native_output() -> None:
    text = read("scripts/release/Finish-NrhisBuildLifecycle.ps1")
    assert "$state = (@(& gh pr view" in text
    assert "$localBranch = (@(& git branch --list" in text
    assert "$remoteBranch = (@(& git ls-remote" in text
    assert "-join \"`n\").Trim()" in text


def test_resume_uses_empty_result_safe_pr_lookup() -> None:
    text = read("scripts/release/Resume-NrhisBuildLifecycle.ps1")
    assert "$PullRequestUrl = (@(& gh pr list" in text
    assert "-join \"`n\").Trim()" in text
    assert "$lifecycle = Join-Path $repo" in text
    assert "Lifecycle helper not found:" in text


def test_archive_requires_verified_receipt_contract() -> None:
    text = read("scripts/release/Finish-NrhisBuildLifecycle.ps1")
    assert "status -ne 'verified'" in text
    assert "verified -ne $true" in text
    assert "Completion receipt is not archive-compatible" in text


def test_historical_lifecycle_features_remain() -> None:
    text = read("scripts/release/Finish-NrhisBuildLifecycle.ps1")
    assert "gh pr checks" in text
    assert "--watch" in text
    assert "gh pr merge" in text
    assert "Complete-Build$BuildNumber.ps1" in text
    assert "Archive-NrhisInstallerArtifacts.ps1" in text
