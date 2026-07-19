from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8-sig")


def test_generic_build_starter_locates_and_extracts_zip() -> None:
    text = read("scripts/release/Start-NrhisBuild.ps1")

    assert "NRHIS_Sprint2_Build${BuildNumber}_OneStep.zip" in text
    assert "Downloads\\$fileName" in text
    assert "Expand-Archive" in text
    assert "Apply-Build$BuildNumber.ps1" in text


def test_generic_build_starter_requires_repository_root() -> None:
    text = read("scripts/release/Start-NrhisBuild.ps1")

    assert 'Test-Path (Join-Path $repoRoot ".git")' in text
    assert "NRHIS repository root not found" in text


def test_completion_removes_temporary_starter_scripts() -> None:
    text = read("scripts/release/Complete-NrhisRelease.ps1")

    assert 'Filter "Start-NRHIS-Build*.ps1"' in text
    assert "Removed temporary starter" in text


def test_release_url_encodes_tag_and_title() -> None:
    text = read("scripts/release/Open-NrhisManualRelease.ps1")

    assert "EscapeDataString($Tag)" in text
    assert "EscapeDataString($ReleaseTitle)" in text
    assert "releases/new?tag=$encodedTag&title=$encodedTitle" in text
