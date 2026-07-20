from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def test_handoff_root_is_outside_repository() -> None:
    text = read("scripts/release/Get-NrhisHandoffRoot.ps1")
    assert "LOCALAPPDATA" in text
    assert "NRHIS\\handoff" in text


def test_operator_handoff_uses_external_root() -> None:
    text = read("scripts/release/New-NrhisOperatorHandoff.ps1")
    assert "Get-NrhisHandoffRoot.ps1" in text
    assert "handoff created outside the repository" in text


def test_section_copy_uses_external_root() -> None:
    text = read("scripts/release/Copy-NrhisHandoffSection.ps1")
    assert "Get-NrhisHandoffRoot.ps1" in text


def test_manual_release_copies_notes_after_browser_opens() -> None:
    text = read("scripts/release/Open-NrhisManualRelease.ps1")
    assert "Start-Process $releaseUrl" in text
    assert "Start-Sleep -Seconds 2" in text
    assert "Get-Content $ReleaseNotesFile -Raw | Set-Clipboard" in text
    assert text.index("Start-Process $releaseUrl") < text.index("Set-Clipboard")


def test_completion_uses_manual_release_helper() -> None:
    text = read("scripts/release/Complete-NrhisRelease.ps1")
    assert "Open-NrhisManualRelease.ps1" in text
