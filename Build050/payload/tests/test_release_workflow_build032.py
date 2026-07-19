from pathlib import Path
import re


STARTER = Path("scripts/release/Start-NrhisBuild.ps1")


def _starter_text() -> str:
    assert STARTER.is_file(), f"missing starter: {STARTER}"
    return STARTER.read_text(encoding="utf-8")


def test_starter_runs_extracted_apply_script() -> None:
    text = _starter_text()
    assert re.search(r'\$entry\s*=\s*Join-Path\s+\$buildFolder', text)
    assert re.search(r'&\s*\$entry\s+@params', text)


def test_starter_reuses_verified_extraction() -> None:
    text = _starter_text()
    assert ".nrhis-extraction.json" in text
    assert "zip_sha256" in text
    assert "Reusing verified Build" in text


def test_starter_supports_force_extract_and_no_chain() -> None:
    text = _starter_text()
    assert re.search(r'\[switch\]\$ForceExtract', text)
    assert re.search(r'\[switch\]\$NoChain', text)
    assert '$params.NoChain = $true' in text
