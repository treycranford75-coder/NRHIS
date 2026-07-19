from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8-sig")


def test_operator_handoff_contains_pr_and_release_metadata() -> None:
    text = read("scripts/release/New-NrhisOperatorHandoff.ps1")

    assert "PullRequestTitle" in text
    assert "PullRequestBodyFile" in text
    assert "ReleaseTag" in text
    assert "ReleaseTitle" in text
    assert "ReleaseNotesFile" in text


def test_operator_handoff_copies_pr_body_and_opens_verified_compare() -> None:
    text = read("scripts/release/New-NrhisOperatorHandoff.ps1")

    assert "Set-Clipboard -Value $pullRequestBody" in text
    assert "compare/${BaseBranch}...${HeadBranch}?expand=1" in text
    assert "Start-Process $compareUrl" in text


def test_handoff_section_helper_supports_all_sections() -> None:
    text = read("scripts/release/Copy-NrhisHandoffSection.ps1")

    for section in (
        "PullRequestTitle",
        "PullRequestBody",
        "ReleaseTitle",
        "ReleaseNotes",
    ):
        assert section in text


def test_completion_prints_release_title_and_tag() -> None:
    text = read("scripts/release/Complete-NrhisRelease.ps1")

    assert 'Write-Host "Release title: $ReleaseTitle"' in text
    assert 'Write-Host "Release tag: $Tag"' in text
