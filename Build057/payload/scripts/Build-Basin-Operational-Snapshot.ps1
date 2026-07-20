[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Split-Path $PSScriptRoot -Parent),
    [switch]$RefreshSources
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo
if ($RefreshSources) {
    & (Join-Path $repo "scripts\Harvest-USGS-Production.ps1")
    & (Join-Path $repo "scripts\Harvest-NWPS-Forecasts.ps1")
}
$env:PYTHONPATH = (Join-Path $repo "src")
& python (Join-Path $repo "scripts\build_basin_operational_snapshot.py") `
    --config (Join-Path $repo "config\nrhis\operational_snapshot.json") `
    --output-root (Join-Path $repo "data\nrhis")
if ($LASTEXITCODE -ne 0) { throw "Basin operational snapshot failed with exit code $LASTEXITCODE" }
