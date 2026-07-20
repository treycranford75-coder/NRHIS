from pathlib import Path

RUNNER = Path("scripts/release/Invoke-NrhisSelfContainedBuild.ps1")
PACKAGER = Path("scripts/release/New-NrhisBuildPackage.ps1")


def test_self_contained_runner_has_required_lifecycle_steps() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    for token in (
        "gh pr create",
        "gh pr checks",
        "no checks reported",
        "gh pr merge",
        "gh release",
        "completion-receipt.json",
        "completion-closure-receipt.json",
        "--force-with-lease",
        "origin/$BaseBranch",
    ):
        assert token in text


def test_runner_does_not_depend_on_legacy_completion_scripts() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert "Complete-NrhisBuild.ps1" not in text
    assert "Finish-NrhisBuildLifecycle.ps1" not in text
    assert "Resume-NrhisBuildLifecycle.ps1" not in text


def test_next_build_packager_creates_zip_and_checksum() -> None:
    text = PACKAGER.read_text(encoding="utf-8")
    assert "Compress-Archive" in text
    assert "Get-FileHash" in text
    assert "OneStep.zip" in text
    assert ".sha256" in text
