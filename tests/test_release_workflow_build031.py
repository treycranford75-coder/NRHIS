from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def test_develop_update_disables_pruning() -> None:
    text = read("scripts/release/Update-NrhisDevelop.ps1")
    assert "git fetch origin --no-prune" in text
    assert "git pull --ff-only --no-prune origin $Branch" in text


def test_release_verifier_uses_parse_safe_prerelease_logic() -> None:
    text = read("scripts/release/Test-NrhisPublishedRelease.ps1")
    assert "$prereleasePassed = $true" in text
    assert "if ($RequirePrerelease)" in text
    assert "prerelease = $prereleasePassed" in text
    assert "prerelease = $(" not in text


def test_powershell_syntax_gate_parses_release_scripts() -> None:
    text = read("scripts/release/Test-NrhisPowerShellSyntax.ps1")
    assert "Language.Parser]::ParseFile" in text
    assert "PowerShell syntax validation failed" in text


def test_ci_parity_runs_powershell_syntax_before_python_gates() -> None:
    text = read("scripts/release/Invoke-NrhisCiParity.ps1")
    syntax_index = text.index('Invoke-Checked "PowerShell syntax"')
    ruff_index = text.index('Invoke-Checked "Ruff"')
    assert syntax_index < ruff_index


def test_completion_uses_no_prune_update_helper() -> None:
    text = read("scripts/release/Complete-NrhisRelease.ps1")
    assert "Update-NrhisDevelop.ps1" in text
