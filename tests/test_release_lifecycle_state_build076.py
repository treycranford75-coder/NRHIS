from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_finish_writes_atomic_lifecycle_state() -> None:
    text = _read("scripts/release/Finish-NrhisBuildLifecycle.ps1")
    assert "function Write-LifecycleState" in text
    assert "lifecycle-state.json" in text
    assert "schema_version = 1" in text
    assert "[System.IO.File]::WriteAllText" in text
    assert "UTF8Encoding" in text


def test_finish_records_major_phases() -> None:
    text = _read("scripts/release/Finish-NrhisBuildLifecycle.ps1")
    for phase in ["initialization", "ci", "merge", "synchronize", "cleanup", "completion", "archive", "closed"]:
        assert f"-Phase '{phase}'" in text


def test_resume_reports_prior_state() -> None:
    text = _read("scripts/release/Resume-NrhisBuildLifecycle.ps1")
    assert "lifecycle-state.json" in text
    assert "Prior lifecycle state:" in text
    assert "ConvertFrom-Json" in text


def test_historical_lifecycle_contracts_remain() -> None:
    text = _read("scripts/release/Finish-NrhisBuildLifecycle.ps1")
    assert "gh pr checks" in text
    assert "--watch" in text
    assert "gh pr merge" in text
    assert "--merge" in text
    assert "git branch --list $featureBranch" in text
    assert "git ls-remote --heads origin" in text
    assert 'Complete-Build$BuildNumber.ps1' in text
    assert "Archive-NrhisInstallerArtifacts.ps1" in text
    assert "Build$BuildNumber completed and verified." in text
