from pathlib import Path


def test_pr_helper_is_idempotent_and_targets_develop() -> None:
    text = Path("scripts/release/New-NrhisPullRequest.ps1").read_text(encoding="utf-8")
    assert "gh pr list" in text
    assert "gh pr create" in text
    assert "--base $Base" in text
    assert "--head $Branch" in text
    assert "Existing pull request:" in text


def test_start_build_creates_pr_after_child_success() -> None:
    text = Path("scripts/release/Start-NrhisBuild.ps1").read_text(encoding="utf-8")
    assert "New-NrhisPullRequest.ps1" in text
    assert "Waiting for CI and merge into develop." in text
    assert "-SkipPullRequest" not in text
    assert "[switch]$SkipPullRequest" in text
    assert "Apply-Build$BuildNumber.ps1" in text


def test_start_build_preserves_checksum_and_entrypoint_gates() -> None:
    text = Path("scripts/release/Start-NrhisBuild.ps1").read_text(encoding="utf-8")
    assert "Get-FileHash" in text
    assert "checksum mismatch" in text
    assert "missing its Build$BuildNumber entry point" in text
