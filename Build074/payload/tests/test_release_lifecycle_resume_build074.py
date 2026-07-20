from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_resume_helper_finds_pr_and_calls_lifecycle() -> None:
    text = _read("scripts/release/Resume-NrhisBuildLifecycle.ps1")
    assert "gh pr list" in text
    assert "--state all" in text
    assert "Finish-NrhisBuildLifecycle.ps1" in text
    assert "-BuildNumber $BuildNumber" in text


def test_finish_lifecycle_is_merge_idempotent() -> None:
    text = _read("scripts/release/Finish-NrhisBuildLifecycle.ps1")
    assert "gh pr view" in text
    assert "$state -ne 'MERGED'" in text
    assert "already merged; continuing closeout" in text


def test_finish_lifecycle_is_closeout_idempotent() -> None:
    text = _read("scripts/release/Finish-NrhisBuildLifecycle.ps1")
    assert "completion-receipt.json" in text
    assert "installer-archive-manifest.json" in text
    assert "skipping duplicate completion" in text
    assert "skipping duplicate archival" in text


def test_failure_messages_include_resume_command() -> None:
    text = _read("scripts/release/Finish-NrhisBuildLifecycle.ps1")
    assert "Resume-NrhisBuildLifecycle.ps1" in text
    assert "CI failed. Automatic merge blocked." in text


def test_legacy_full_lifecycle_contracts_remain() -> None:
    text = _read("scripts/release/Finish-NrhisBuildLifecycle.ps1")
    assert "gh pr checks" in text
    assert "--watch" in text
    assert "gh pr merge" in text
    assert "--merge" in text
    assert 'Complete-Build$BuildNumber.ps1' in text
    assert "Archive-NrhisInstallerArtifacts.ps1" in text
