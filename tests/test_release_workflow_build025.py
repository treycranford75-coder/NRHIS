from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8-sig")


def test_preflight_checks_required_environment() -> None:
    text = read("scripts/release/Test-NrhisReleaseEnvironment.ps1")

    assert "Git installed" in text
    assert "Python installed" in text
    assert "Repository match" in text
    assert "Branch match" in text
    assert "Working tree clean" in text
    assert "GitHub CLI authenticated" in text


def test_github_cli_bootstrap_is_explicit() -> None:
    text = read("scripts/release/Initialize-NrhisGitHubCli.ps1")

    assert "winget install --id GitHub.cli" in text
    assert "if (($null -eq $gh) -and $Install)" in text
    assert "gh auth login" in text
    assert "-Authenticate" in text


def test_existing_release_publisher_requires_tag_and_authentication() -> None:
    text = read("scripts/release/Publish-NrhisExistingRelease.ps1")

    assert "git show-ref --tags --verify" in text
    assert "git ls-remote --exit-code --tags origin" in text
    assert "gh auth status" in text
    assert "gh release create $Tag" in text
    assert "--prerelease" in text


def test_existing_release_publisher_rejects_duplicate_release() -> None:
    text = read("scripts/release/Publish-NrhisExistingRelease.ps1")

    assert "gh release view $Tag" in text
    assert "A GitHub release already exists" in text
