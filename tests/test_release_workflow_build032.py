from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def test_branch_initializer_uses_no_prune_sync() -> None:
    text = read("scripts/release/Initialize-NrhisBuildBranch.ps1")
    assert "git fetch origin --no-prune" in text
    assert "git pull --ff-only --no-prune origin $BaseBranch" in text


def test_branch_initializer_creates_feature_from_base() -> None:
    text = read("scripts/release/Initialize-NrhisBuildBranch.ps1")
    assert "git switch -c $FeatureBranch $BaseBranch" in text


def test_payload_installer_supports_bootstrap_files() -> None:
    text = read("scripts/release/Install-NrhisBuildPayload.ps1")
    assert "BootstrapFiles" in text
    assert "Install-RelativeFile" in text


def test_build032_documents_bootstrap_before_branch_setup() -> None:
    text = read("docs/Release/Sprint2_Build032_PR.md")
    assert "bootstrap helpers before branch setup" in text.lower()
    assert "commit on `develop`" in text


def test_starter_runs_extracted_apply_script() -> None:
    text = read("scripts/release/Start-NrhisBuild.ps1")
    assert "& $applyScript" in text
    assert "Apply script not found after extraction" in text
