from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_start_build_invokes_full_lifecycle() -> None:
    text = _read("scripts/release/Start-NrhisBuild.ps1")
    assert "Finish-NrhisBuildLifecycle.ps1" in text
    assert "-PullRequestUrl $prUrl" in text
    assert "[switch]$SkipLifecycle" in text
    assert "[switch]$SkipArchive" in text


def test_lifecycle_watches_checks_and_merges() -> None:
    text = _read("scripts/release/Finish-NrhisBuildLifecycle.ps1")
    assert "gh pr checks" in text
    assert "--watch" in text
    assert "--fail-fast" in text
    assert "gh pr merge" in text
    assert "--merge" in text


def test_lifecycle_completes_and_archives() -> None:
    text = _read("scripts/release/Finish-NrhisBuildLifecycle.ps1")
    assert 'Complete-Build$BuildNumber.ps1' in text
    assert "Archive-NrhisInstallerArtifacts.ps1" in text
    assert 'Build$BuildNumber completed and verified.' in text


def test_legacy_workflow_contracts_are_retained() -> None:
    text = _read("scripts/release/Start-NrhisBuild.ps1")
    assert "[switch]$ForceExtract" in text
    assert "[switch]$NoChain" in text
    assert ".nrhis-extraction.json" in text
    assert "Apply-Build$BuildNumber.ps1" in text
