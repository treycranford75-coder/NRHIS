[CmdletBinding()]
param(
    [string]$StartDate = '2017-09-01',
    [string]$EndDate = '2018-06-30',
    [string]$SiteNo = '08211503',
    [string]$RepositoryRoot = (Get-Location).Path,
    [string]$OutputRoot,
    [int]$CadenceMinutes = 15,
    [double]$GapHours = 24.0
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$csv = Join-Path $repo 'data/nrhis/normalized/usgs_historical_observations.csv'
$index = Join-Path $repo 'data/nrhis/backfill/usgs_history_query_index.json'
$script = Join-Path $repo 'scripts/analyze_rincon_evidence_reconciliation.py'
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $repo 'data/nrhis/analysis'
}
if (-not (Test-Path $csv -PathType Leaf)) { throw "Finalized historical CSV not found: $csv" }
if (-not (Test-Path $index -PathType Leaf)) { throw "Historical query index not found: $index" }
if (-not (Test-Path $script -PathType Leaf)) { throw "Rincon evidence analysis script not found: $script" }

Write-Host 'NRHIS Rincon interval reconciliation and evidence timeline' -ForegroundColor Cyan
Write-Host "Range:  $StartDate through $EndDate"
Write-Host "Site:   $SiteNo"
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
    '--gap-hours', [string]$GapHours
)
& python @argsList
if ($LASTEXITCODE -ne 0) { throw "NRHIS Rincon evidence reconciliation failed with exit code $LASTEXITCODE." }
