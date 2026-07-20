from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_preflight_checks_required_release_scripts() -> None:
    text = read("scripts/release/Test-NrhisReleaseLifecycle.ps1")
    for name in (
        "Start-NrhisBuild.ps1",
        "New-NrhisPullRequest.ps1",
        "Finish-NrhisBuildLifecycle.ps1",
        "Resume-NrhisBuildLifecycle.ps1",
        "Complete-NrhisBuild.ps1",
        "Archive-NrhisInstallerArtifacts.ps1",
    ):
        assert name in text


def test_preflight_checks_completion_and_archive_contracts() -> None:
    text = read("scripts/release/Test-NrhisReleaseLifecycle.ps1")
    assert "status -ne 'verified'" in text
    assert "verified -ne $true" in text
    assert "status = 'verified'" in text
    assert "verified = $true" in text
    assert "gh release view" in text
    assert "gh release create" in text


def test_preflight_checks_idempotent_branch_cleanup() -> None:
    text = read("scripts/release/Test-NrhisReleaseLifecycle.ps1")
    assert "Local feature branch already absent:" in text
    assert "Remote feature branch already absent:" in text


def test_preflight_writes_machine_readable_receipt() -> None:
    text = read("scripts/release/Test-NrhisReleaseLifecycle.ps1")
    assert "lifecycle-preflight.json" in text
    assert "healthy = ($problems.Count -eq 0)" in text
    assert "problem_count = $problems.Count" in text
    assert "ConvertTo-Json" in text
