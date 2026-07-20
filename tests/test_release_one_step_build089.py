from pathlib import Path

RUNNER = Path("scripts/release/Invoke-NrhisSelfContainedBuild.ps1")
APPLY = Path("Build089/Apply-Build089.ps1")
PACKAGER = Path("scripts/release/New-NrhisBuildPackage.ps1")


def test_runner_uses_develop_and_explicit_staging_allowlist() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert "[string]$BaseBranch = 'develop'" in text
    assert "[string[]]$StagedPaths" in text
    assert "git add -A" in text  # Appears only in the prohibition comment.
    assert "Never replace this with git add -A" in text
    assert "(@('add', '--') + $StagedPaths)" in text


def test_runner_blocks_generated_data_and_large_blobs() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert "data/nrhis/(raw|normalized|operations_cycles)" in text
    assert "95000000" in text
    assert "git cat-file" in text


def test_runner_has_noninteractive_and_recoverable_lifecycle() -> None:
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
        "core.editor=true",
        "full local test suite passed",
    ):
        assert token in text
    assert "Complete-NrhisBuild.ps1" not in text
    assert "Finish-NrhisBuildLifecycle.ps1" not in text
    assert "Resume-NrhisBuildLifecycle.ps1" not in text


def test_apply_prepares_branch_before_copying_payload() -> None:
    text = APPLY.read_text(encoding="utf-8")
    assert "origin/$baseBranch" in text
    assert "feature/sprint2-build$buildNumber" in text
    assert text.index("Invoke-Git @('switch'") < text.index("foreach ($file in $payloadFiles)")
    assert "Tracked working-tree changes are present. Build089 made no changes." in text


def test_packager_creates_zip_and_checksum() -> None:
    text = PACKAGER.read_text(encoding="utf-8")
    assert "Compress-Archive" in text
    assert "Get-FileHash" in text
    assert "OneStep.zip" in text
    assert ".sha256" in text
