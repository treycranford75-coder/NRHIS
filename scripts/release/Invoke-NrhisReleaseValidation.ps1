[CmdletBinding()]
param(
    [int]$MinimumCoverage = 80
)

$ErrorActionPreference = "Stop"

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Description,

        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Description" -ForegroundColor Cyan
    & $Command

    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

Invoke-CheckedCommand "Full pytest suite" {
    python -m pytest -q
}

Invoke-CheckedCommand "Ruff checks" {
    python -m ruff check .
}

Invoke-CheckedCommand "Coverage gate" {
    python -m pytest -q `
        --cov=src `
        --cov-branch `
        --cov-report=term-missing `
        --cov-report=xml `
        --cov-fail-under=$MinimumCoverage
}

Invoke-CheckedCommand "Legacy preservation tests" {
    python -m pytest -q .\tests\test_legacy_preservation.py
}

Invoke-CheckedCommand "Git whitespace check" {
    git diff --check
}

Write-Host ""
Write-Host "NRHIS release validation passed." -ForegroundColor Green
