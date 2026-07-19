from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def test_release_evidence_root_is_outside_repository() -> None:
    text = read("scripts/release/Get-NrhisReleaseEvidenceRoot.ps1")
    assert "LOCALAPPDATA" in text
    assert 'NRHIS\\release-evidence' in text


def test_published_release_verifier_checks_required_fields() -> None:
    text = read("scripts/release/Test-NrhisPublishedRelease.ps1")
    for expected in (
        "tag_name",
        "title",
        "prerelease",
        "draft_false",
        "notes_exact",
        "published_url_present",
    ):
        assert expected in text


def test_published_release_verifier_uses_public_github_api() -> None:
    text = read("scripts/release/Test-NrhisPublishedRelease.ps1")
    assert "api.github.com/repos/$repository/releases/tags/$Tag" in text
    assert "Invoke-RestMethod" in text
    assert "User-Agent" in text


def test_release_verifier_writes_machine_readable_evidence() -> None:
    text = read("scripts/release/Test-NrhisPublishedRelease.ps1")
    assert "ConvertTo-Json -Depth 8" in text
    assert "release_verification.json" in text
    assert "failed_checks" in text


def test_release_waiter_has_bounded_polling() -> None:
    text = read("scripts/release/Wait-NrhisPublishedRelease.ps1")
    assert "TimeoutMinutes" in text
    assert "PollSeconds" in text
    assert "Start-Sleep" in text
    assert "Timed out waiting" in text
