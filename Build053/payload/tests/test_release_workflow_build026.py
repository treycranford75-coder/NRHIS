from pathlib import Path
import re


STARTER = Path("scripts/release/Start-NrhisBuild.ps1")


def _starter_text() -> str:
    assert STARTER.is_file(), f"missing starter: {STARTER}"
    return STARTER.read_text(encoding="utf-8")


def test_generic_build_starter_locates_and_extracts_zip() -> None:
    text = _starter_text()
    assert re.search(r"NRHIS_Sprint2_Build\$\{BuildNumber\}_OneStep\.zip", text)
    assert 'Join-Path $HOME "Downloads"' in text
    assert "Expand-Archive" in text
    assert re.search(r"Apply-Build.*BuildNumber.*\.ps1", text)


def test_generic_build_starter_requires_repository_root() -> None:
    text = _starter_text()
    assert re.search(r'Test-Path\s*\(Join-Path\s+\$repo\s+"\.git"\)', text)
    assert "Run from the NRHIS repository root" in text


def test_generic_build_starter_validates_checksum() -> None:
    text = _starter_text()
    assert "Get-FileHash" in text
    assert "SHA256" in text
    assert "Build ZIP checksum mismatch" in text
