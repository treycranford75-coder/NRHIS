from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_completion_helper_emits_archive_compatible_receipt() -> None:
    text = _read("scripts/release/Complete-NrhisBuild.ps1")
    assert "status = 'verified'" in text
    assert "verified = $true" in text
    assert "completion-receipt.json" in text


def test_release_lookup_tolerates_missing_release() -> None:
    text = _read("scripts/release/Complete-NrhisBuild.ps1")
    assert "PSNativeCommandUseErrorActionPreference" in text
    assert "$releaseViewExitCode" in text
    assert "$existingLines -join" in text
    assert "gh release view" in text


def test_native_outputs_are_empty_result_safe() -> None:
    text = _read("scripts/release/Complete-NrhisBuild.ps1")
    assert "@(& (Join-Path $repo 'scripts/release/Get-NrhisGitHubRepository.ps1')) -join" in text
    assert "$releaseLines -join" in text


def test_build078_wrapper_targets_verified_helper() -> None:
    text = _read("Build078/Complete-Build078.ps1")
    assert "Complete-NrhisBuild.ps1" in text
    assert "-BuildNumber '078'" in text
    assert "-Tag 'v0.1.1-rc78+build078'" in text


def test_apply_script_avoids_self_copy() -> None:
    text = _read("Build078/Apply-Build078.ps1")
    assert "OrdinalIgnoreCase" in text
    assert "sourcePath.Equals" in text
