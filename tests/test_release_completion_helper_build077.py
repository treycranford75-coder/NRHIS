from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_generic_completion_helper_is_installed() -> None:
    text = _read("scripts/release/Complete-NrhisBuild.ps1")
    assert "[string]$BuildNumber" in text
    assert "gh release create" in text
    assert "completion-receipt.json" in text
    assert "GitHub pre-release already exists" in text


def test_build077_wrapper_targets_generic_helper() -> None:
    text = _read("Build077/Complete-Build077.ps1")
    assert "Complete-NrhisBuild.ps1" in text
    assert "-BuildNumber '077'" in text
    assert "-Tag 'v0.1.1-rc77+build077'" in text


def test_finish_lifecycle_uses_build_wrapper() -> None:
    text = _read("scripts/release/Finish-NrhisBuildLifecycle.ps1")
    assert '"Build$BuildNumber\\Complete-Build$BuildNumber.ps1"' in text
