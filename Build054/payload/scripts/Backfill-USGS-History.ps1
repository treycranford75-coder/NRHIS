[CmdletBinding()]
param(
    [string]$StartDate = "2024-02-01",
    [string]$EndDate = (Get-Date -Format "yyyy-MM-dd"),
    [int]$ChunkDays = 7,
    [string]$OutputRoot = (Join-Path (Get-Location).Path "data\nrhis"),
    [switch]$NoResume
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$repo = (Get-Location).Path
$config = Join-Path $repo "config\nrhis\usgs_nueces_basin.json"
$script = Join-Path $repo "scripts\backfill_usgs_history.py"
if (-not (Test-Path $config)) { throw "Missing USGS basin configuration: $config" }
if (-not (Test-Path $script)) { throw "Missing historical backfill script: $script" }
$env:PYTHONPATH = (Join-Path $repo "src")
$argsList = @(
    $script,
    "--config", $config,
    "--output-root", $OutputRoot,
    "--start-date", $StartDate,
    "--end-date", $EndDate,
    "--chunk-days", [string]$ChunkDays
)
if ($NoResume) { $argsList += "--no-resume" }
& python @argsList
if ($LASTEXITCODE -ne 0) { throw "USGS historical backfill failed with exit code $LASTEXITCODE." }
