from pathlib import Path

RUNNER = Path("scripts/release/Invoke-NrhisSelfContainedBuild.ps1")


def test_installer_archive_guard_parenthesizes_each_test_path() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    old = "if (Test-Path $buildDirectory -PathType Container -and Test-Path $packager -PathType Leaf) {"
    new = "if ((Test-Path $buildDirectory -PathType Container) -and (Test-Path $packager -PathType Leaf)) {"
    assert old not in text
    assert new in text


def test_installer_archive_path_and_packager_contract_remain() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    for token in (
        "$installerArchive = Join-Path $evidenceRoot 'installer-archive'",
        "$buildDirectory = Join-Path $repo \"Build$BuildNumber\"",
        "$packager = Join-Path $repo 'scripts/release/New-NrhisBuildPackage.ps1'",
        "& $packager -BuildNumber $BuildNumber -SourceDirectory $buildDirectory -OutputDirectory $installerArchive",
        'throw "Build$BuildNumber installer archive generation failed."',
    ):
        assert token in text
