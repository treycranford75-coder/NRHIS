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
    [int]$MinPairedHours = 48,
    [int]$PercentileStep = 5,
    [int]$MinTransitionPercentile = 60,
    [int]$MaxTransitionPercentile = 90,
    [double]$CoherenceR = 0.8,
    [double]$StrongR = 0.9,
    [double]$MaxLowerR = 0.5,
    [int]$ConfirmSteps = 2,
    [int]$BandWidthPercentile = 20,
    [int]$EventGapToleranceHours = 2,
    [int]$MinEventHighHours = 12,
    [int]$EventMinPairedHours = 6
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$csv = Join-Path $repo 'data/nrhis/normalized/usgs_historical_observations.csv'
$index = Join-Path $repo 'data/nrhis/backfill/usgs_history_query_index.json'
$script = Join-Path $repo 'scripts/analyze_lower_nueces_flow_transition_contrast.py'
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $repo 'data/nrhis/analysis'
}

if (-not (Test-Path $csv -PathType Leaf)) { throw "Finalized historical CSV not found: $csv" }
if (-not (Test-Path $index -PathType Leaf)) { throw "Historical query index not found: $index" }
if (-not (Test-Path $script -PathType Leaf)) { throw "Lower Nueces flow-transition script not found: $script" }

Write-Host 'NRHIS lower Nueces upper-flow transition contrast analysis' -ForegroundColor Cyan
Write-Host "Range:  $StartDate through $EndDate"
Write-Host 'Sites:  08211000 Mathis -> 08211200 Bluntzer -> 08211500 Calallen'
Write-Host 'Param:  00060 discharge'
Write-Host 'Mode:   local-only; zero USGS requests' -ForegroundColor Green
Write-Host 'Method: disjoint lower/upper subsets plus non-overlapping flow bands.' -ForegroundColor Yellow
Write-Host 'Note:   Build103 cumulative onset is not used as an event threshold.' -ForegroundColor Yellow
Write-Host 'Note:   residuals are descriptive and are not a reach water balance.' -ForegroundColor Yellow

$argsList = @(
    $script,
    '--csv', $csv,
    '--index', $index,
    '--start', $StartDate,
    '--end', $EndDate,
    '--output-root', $OutputRoot,
    '--min-observations-per-hour', [string]$MinObservationsPerHour,
    '--max-lag-hours', [string]$MaxLagHours,
    '--min-paired-hours', [string]$MinPairedHours,
    '--percentile-step', [string]$PercentileStep,
    '--min-transition-percentile', [string]$MinTransitionPercentile,
    '--max-transition-percentile', [string]$MaxTransitionPercentile,
    '--coherence-r', [string]$CoherenceR,
    '--strong-r', [string]$StrongR,
    '--max-lower-r', [string]$MaxLowerR,
    '--confirm-steps', [string]$ConfirmSteps,
    '--band-width-percentile', [string]$BandWidthPercentile,
    '--event-gap-tolerance-hours', [string]$EventGapToleranceHours,
    '--min-event-high-hours', [string]$MinEventHighHours,
    '--event-min-paired-hours', [string]$EventMinPairedHours
)

& python @argsList
if ($LASTEXITCODE -ne 0) {
    throw "NRHIS lower Nueces flow-transition analysis failed with exit code $LASTEXITCODE."
}
