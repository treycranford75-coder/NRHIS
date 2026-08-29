[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$StartDate,

    [Parameter(Mandatory = $true)]
    [string]$EndDate,

    [string[]]$SiteNo = @(),
    [string[]]$ParameterCode = @(),
    [string]$RepositoryRoot = (Get-Location).Path,
    [string]$OutputRoot,
    [int]$StrideRows = 50000,
    [int]$Limit = 0,
    [switch]$RebuildIndex
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# Normalize values crossing the powershell.exe -File boundary.
# A [string[]] may arrive as one comma-delimited string.
$NormalizedSiteNos = @(
    foreach ($raw in @($SiteNo)) {
        foreach ($value in ([string]$raw -split ',')) {
            $value = $value.Trim()
            if ($value) {
                $value
            }
        }
    }
)

$NormalizedParameterCodes = @(
    foreach ($raw in @($ParameterCode)) {
        foreach ($value in ([string]$raw -split ',')) {
            $value = $value.Trim()
            if ($value) {
                $value
            }
        }
    }
)

$repo = (Resolve-Path $RepositoryRoot).Path
$csv = Join-Path $repo 'data/nrhis/normalized/usgs_historical_observations.csv'
$index = Join-Path $repo 'data/nrhis/backfill/usgs_history_query_index.json'
$script = Join-Path $repo 'scripts/query_usgs_history.py'
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $repo 'data/nrhis/queries'
}

if (-not (Test-Path $csv -PathType Leaf)) {
    throw "Finalized historical CSV not found: $csv"
}
if (-not (Test-Path $script -PathType Leaf)) {
    throw "Historical query script not found: $script"
}

Write-Host 'NRHIS finalized historical archive query' -ForegroundColor Cyan
Write-Host "Range:  $StartDate through $EndDate"
Write-Host "CSV:    $csv"
Write-Host "Index:  $index"
Write-Host 'Mode:   local-only; zero USGS requests' -ForegroundColor Green
if ($NormalizedSiteNos.Count -gt 0) {
    Write-Host "Sites:  $($NormalizedSiteNos -join ', ')"
}
if ($NormalizedParameterCodes.Count -gt 0) {
    Write-Host "Params: $($NormalizedParameterCodes -join ', ')"
}

$argsList = @(
    $script,
    '--csv', $csv,
    '--index', $index,
    '--start', $StartDate,
    '--end', $EndDate,
    '--output-root', $OutputRoot,
    '--stride-rows', [string]$StrideRows
)
foreach ($site in $NormalizedSiteNos) {
    $argsList += @('--site', $site)
}
foreach ($parameter in $NormalizedParameterCodes) {
    $argsList += @('--parameter', $parameter)
}
if ($Limit -gt 0) {
    $argsList += @('--limit', [string]$Limit)
}
if ($RebuildIndex) {
    $argsList += '--rebuild-index'
}

& python @argsList
if ($LASTEXITCODE -ne 0) {
    throw "NRHIS historical query failed with exit code $LASTEXITCODE."
}
