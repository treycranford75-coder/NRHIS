from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def test_verification_command_contains_required_metadata() -> None:
    text = read("scripts/release/Get-NrhisReleaseVerificationCommand.ps1")
    assert "Wait-NrhisPublishedRelease.ps1" in text
    assert "-Tag" in text
    assert "-ExpectedTitle" in text
    assert "-ExpectedNotesFile" in text
    assert "-TimeoutMinutes" in text


def test_verification_handoff_is_external() -> None:
    text = read("scripts/release/New-NrhisReleaseVerificationHandoff.ps1")
    assert "Get-NrhisHandoffRoot.ps1" in text
    assert "Get-NrhisReleaseEvidenceRoot.ps1" in text
    assert "Set-Clipboard" in text


def test_manual_completion_creates_verification_handoff() -> None:
    text = read("scripts/release/Complete-NrhisRelease.ps1")
    assert "Open-NrhisManualRelease.ps1" in text
    assert "New-NrhisReleaseVerificationHandoff.ps1" in text


def test_authenticated_completion_verifies_published_release() -> None:
    text = read("scripts/release/Complete-NrhisRelease.ps1")
    assert "gh release create" in text
    assert "Wait-NrhisPublishedRelease.ps1" in text
    assert "published and verified successfully" in text


def test_build034_documents_post_publish_handoff() -> None:
    text = read("docs/Release/Sprint2_Build034_PR.md")
    assert "post-publication verification handoff" in text.lower()
    assert "evidence" in text.lower()
