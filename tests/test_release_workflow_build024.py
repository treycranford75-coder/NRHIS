from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8-sig")


def test_repository_parser_supports_common_github_remotes() -> None:
    text = read("scripts/release/Get-NrhisGitHubRepository.ps1")

    assert "git@github\\.com:" in text
    assert "https://github\\.com/" in text
    assert "Unsupported GitHub origin remote" in text


def test_pull_request_fallback_uses_explicit_base_and_head() -> None:
    text = read("scripts/release/New-NrhisPullRequest.ps1")

    assert "compare/${BaseBranch}...${HeadBranch}?expand=1" in text
    assert "--base $BaseBranch" in text
    assert "--head $HeadBranch" in text


def test_release_fallback_preserves_markdown_and_prefills_tag() -> None:
    text = read("scripts/release/Complete-NrhisRelease.ps1")

    assert "Get-Content $ReleaseNotesFile -Raw | Set-Clipboard" in text
    assert "releases/new?tag=$encodedTag&title=$encodedTitle" in text
    assert "--notes-file $ReleaseNotesFile" in text


def test_manual_copy_script_uses_raw_content() -> None:
    text = read("scripts/release/Copy-NrhisReleaseNotes.ps1")

    assert "Get-Content $ReleaseNotesFile -Raw" in text
    assert "Set-Clipboard -Value $content" in text
