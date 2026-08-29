[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [string]$OutputRoot,
    [string]$Title = 'NRHIS Rincon Bayou Evidence Report'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$analysisRoot = Join-Path $repo 'data/nrhis/analysis'
$script = Join-Path $repo 'scripts/generate_rincon_evidence_report.py'
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $repo 'reports/nrhis'
}
if (-not (Test-Path $script -PathType Leaf)) {
    throw "Rincon evidence report script not found: $script"
}

$latest = Get-ChildItem $analysisRoot -Directory -Filter 'rincon-evidence-*' -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if (-not $latest) {
    throw "No Build099 rincon-evidence-* analysis directory found under $analysisRoot"
}

$summary = Join-Path $latest.FullName 'rincon_evidence_reconciliation_summary.json'
$receipt = Join-Path $latest.FullName 'analysis-receipt.json'
if (-not (Test-Path $summary -PathType Leaf)) { throw "Build099 summary not found: $summary" }
if (-not (Test-Path $receipt -PathType Leaf)) { throw "Build099 receipt not found: $receipt" }

Write-Host 'NRHIS formal Rincon evidence report' -ForegroundColor Cyan
Write-Host "Build099 evidence: $($latest.FullName)"
Write-Host 'Mode: local-only; zero USGS requests' -ForegroundColor Green

$argsList = @(
    $script,
    '--build099-summary', $summary,
    '--build099-receipt', $receipt,
    '--output-root', $OutputRoot,
    '--title', $Title
)
& python @argsList
if ($LASTEXITCODE -ne 0) {
    throw "NRHIS Rincon evidence report generation failed with exit code $LASTEXITCODE."
}
