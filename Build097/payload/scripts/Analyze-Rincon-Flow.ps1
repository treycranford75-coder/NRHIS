[CmdletBinding()]
param(
    [string]$StartDate = '2007-01-01',
    [string]$EndDate = '2026-08-29',
    [string]$SiteNo = '08211503',
    [string]$RepositoryRoot = (Get-Location).Path,
    [string]$OutputRoot,
    [int]$CadenceMinutes = 15,
    [double]$GapHours = 24.0,
    [double]$StageContinuityRatio = 0.80
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$csv = Join-Path $repo 'data/nrhis/normalized/usgs_historical_observations.csv'
$index = Join-Path $repo 'data/nrhis/backfill/usgs_history_query_index.json'
$script = Join-Path $repo 'scripts/analyze_rincon_flow.py'
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $repo 'data/nrhis/analysis'
}

if (-not (Test-Path $csv -PathType Leaf)) {
    throw "Finalized historical CSV not found: $csv"
}
if (-not (Test-Path $index -PathType Leaf)) {
    throw "Historical query index not found: $index"
}
if (-not (Test-Path $script -PathType Leaf)) {
    throw "Rincon analysis script not found: $script"
}

Write-Host 'NRHIS Rincon discontinuity and directional-flow analysis' -ForegroundColor Cyan
Write-Host "Range:  $StartDate through $EndDate"
Write-Host "Site:   $SiteNo"
Write-Host "Gap:    $GapHours hour(s)"
Write-Host 'Mode:   local-only; zero USGS requests' -ForegroundColor Green

$argsList = @(
    $script,
    '--csv', $csv,
    '--index', $index,
    '--start', $StartDate,
    '--end', $EndDate,
    '--site', $SiteNo,
    '--output-root', $OutputRoot,
    '--cadence-minutes', [string]$CadenceMinutes,
    '--gap-hours', [string]$GapHours,
    '--stage-continuity-ratio', [string]$StageContinuityRatio
)

& python @argsList
if ($LASTEXITCODE -ne 0) {
    throw "NRHIS Rincon flow analysis failed with exit code $LASTEXITCODE."
}
