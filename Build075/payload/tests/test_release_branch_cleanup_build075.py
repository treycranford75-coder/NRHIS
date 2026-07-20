from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_finish_checks_local_branch_before_delete() -> None:
    text = _read("scripts/release/Finish-NrhisBuildLifecycle.ps1")
    assert "git branch --list $featureBranch" in text
    assert "Local feature branch already absent" in text
    assert "git branch -D $featureBranch" in text


def test_finish_checks_remote_branch_before_delete() -> None:
    text = _read("scripts/release/Finish-NrhisBuildLifecycle.ps1")
    assert "git ls-remote --heads origin" in text
    assert 'refs/heads/$featureBranch' in text
    assert "Remote feature branch already absent" in text
    assert "git push origin --delete $featureBranch" in text


def test_absent_branches_are_nonfatal() -> None:
    text = _read("scripts/release/Finish-NrhisBuildLifecycle.ps1")
    local_absent = text.index("Local feature branch already absent")
    remote_absent = text.index("Remote feature branch already absent")
    assert "throw" not in text[local_absent : local_absent + 120]
    assert "throw" not in text[remote_absent : remote_absent + 120]


def test_resume_still_delegates_to_finish_helper() -> None:
    text = _read("scripts/release/Resume-NrhisBuildLifecycle.ps1")
    assert "Finish-NrhisBuildLifecycle.ps1" in text
    assert "-BuildNumber $BuildNumber" in text
    assert "-SkipArchive:$SkipArchive" in text


def test_historical_lifecycle_contracts_remain() -> None:
    text = _read("scripts/release/Finish-NrhisBuildLifecycle.ps1")
    assert "gh pr checks" in text
    assert "--watch" in text
    assert "gh pr merge" in text
    assert "--merge" in text
    assert 'Complete-Build$BuildNumber.ps1' in text
    assert "Archive-NrhisInstallerArtifacts.ps1" in text
    assert "Build$BuildNumber completed and verified." in text
