[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$StartDate,

    [Parameter(Mandatory = $true)]
    [string]$EndDate,

    [string]$RepositoryRoot = (Get-Location).Path,
    [string]$OutputRoot,
    [int]$MinObservationsPerHour = 2,
    [int]$MaxLagHours = 72,
    [int]$MinPairedHours = 48
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$csv = Join-Path $repo 'data/nrhis/normalized/usgs_historical_observations.csv'
$index = Join-Path $repo 'data/nrhis/backfill/usgs_history_query_index.json'
$script = Join-Path $repo 'scripts/analyze_lower_nueces_flow_network.py'
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $repo 'data/nrhis/analysis'
}

if (-not (Test-Path $csv -PathType Leaf)) { throw "Finalized historical CSV not found: $csv" }
if (-not (Test-Path $index -PathType Leaf)) { throw "Historical query index not found: $index" }
if (-not (Test-Path $script -PathType Leaf)) { throw "Lower Nueces analysis script not found: $script" }

Write-Host 'NRHIS lower Nueces station-to-station discharge analysis' -ForegroundColor Cyan
Write-Host "Range:  $StartDate through $EndDate"
Write-Host 'Sites:  08211000 Mathis -> 08211200 Bluntzer -> 08211500 Calallen'
Write-Host 'Param:  00060 discharge'
Write-Host 'Mode:   local-only; zero USGS requests' -ForegroundColor Green
Write-Host 'Note:   lag correlation is descriptive; it is not proof of physical travel time.' -ForegroundColor Yellow

$argsList = @(
    $script,
    '--csv', $csv,
    '--index', $index,
    '--start', $StartDate,
    '--end', $EndDate,
    '--output-root', $OutputRoot,
    '--min-observations-per-hour', [string]$MinObservationsPerHour,
    '--max-lag-hours', [string]$MaxLagHours,
    '--min-paired-hours', [string]$MinPairedHours
)

& python @argsList
if ($LASTEXITCODE -ne 0) {
    throw "NRHIS lower Nueces analysis failed with exit code $LASTEXITCODE."
}
