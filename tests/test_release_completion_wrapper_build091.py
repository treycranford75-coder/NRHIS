from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def test_completion_wrapper_generator_contract() -> None:
    script = (REPO / "scripts" / "release" / "New-NrhisCompletionWrapper.ps1").read_text(
        encoding="utf-8"
    )
    assert "[string]$RepositoryRoot" in script
    assert "Complete-NrhisBuild.ps1" in script
    assert "Complete-Build$BuildNumber.ps1" in script
    assert "ParseFile" in script
    assert "Generated completion wrapper does not accept -RepositoryRoot" in script


def test_self_contained_lifecycle_generates_and_stages_wrapper() -> None:
    script = (
        REPO / "scripts" / "release" / "Invoke-NrhisSelfContainedBuild.ps1"
    ).read_text(encoding="utf-8")
    assert "New-NrhisCompletionWrapper.ps1" in script
    assert 'Build$BuildNumber/Complete-Build$BuildNumber.ps1' in script
    assert "$StagedPaths = @($StagedPaths) + $wrapperRelativePath" in script
    assert "(@('add', '--') + $StagedPaths)" in script
    assert "staged_paths = $StagedPaths" in script


def test_finish_lifecycle_consumes_generated_wrapper() -> None:
    script = (
        REPO / "scripts" / "release" / "Finish-NrhisBuildLifecycle.ps1"
    ).read_text(encoding="utf-8")
    assert '"Build$BuildNumber\\Complete-Build$BuildNumber.ps1"' in script
    assert "-RepositoryRoot $repo" in script
    assert "completion-receipt.json" in script


def test_starter_skips_duplicate_legacy_lifecycle_after_self_contained_closeout() -> None:
    script = (REPO / "scripts" / "release" / "Start-NrhisBuild.ps1").read_text(
        encoding="utf-8"
    )
    assert "completion-closure-receipt.json" in script
    assert "self-contained lifecycle already completed; legacy outer lifecycle skipped" in script
    assert "$branchAfterChild -eq 'develop'" in script
