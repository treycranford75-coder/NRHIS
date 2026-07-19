[CmdletBinding()]
param(
    [int]$MinimumCoverage = 80
)

$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Name" -ForegroundColor Cyan
    & $Command

    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE."
    }
}

Invoke-Checked "Ruff" {
    python -m ruff check .
}

Invoke-Checked "Full pytest suite" {
    python -m pytest -q
}

Invoke-Checked "Branch coverage" {
    python -m pytest -q `
        --cov=src `
        --cov-branch `
        --cov-report=term-missing `
        --cov-report=xml `
        --cov-fail-under=$MinimumCoverage
}

Invoke-Checked "Legacy preservation tests" {
    python -m pytest -q .\tests\test_legacy_preservation.py
}

Invoke-Checked "Git whitespace check" {
    git diff --check
}

Write-Host ""
Write-Host "NRHIS CI-parity validation passed." -ForegroundColor Green
