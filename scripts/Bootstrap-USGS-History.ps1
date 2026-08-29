[CmdletBinding()]
param(
    [string]$StartDate = "2007-01-01",
    [string]$EndDate = (Get-Date -Format "yyyy-MM-dd"),
    [int]$ChunkDays = 7,
    [string]$OutputRoot = (Join-Path (Get-Location).Path "data\nrhis"),
    [switch]$NoResume,
    [switch]$PlanOnly
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Get-Location).Path
$runner = Join-Path $repo "scripts\Backfill-USGS-History.ps1"
$configPath = Join-Path $repo "config\nrhis\usgs_nueces_basin.json"

if (-not (Test-Path $runner -PathType Leaf)) {
    throw "Missing historical backfill runner: $runner"
}
if (-not (Test-Path $configPath -PathType Leaf)) {
    throw "Missing USGS basin configuration: $configPath"
}
if ($ChunkDays -lt 1) {
    throw "ChunkDays must be at least 1."
}

$start = [datetime]::ParseExact($StartDate, "yyyy-MM-dd", $null)
$end = [datetime]::ParseExact($EndDate, "yyyy-MM-dd", $null)
if ($end -lt $start) {
    throw "EndDate cannot precede StartDate."
}

$config = Get-Content $configPath -Raw | ConvertFrom-Json
$days = [int](($end.Date - $start.Date).TotalDays + 1)
$chunks = [int][math]::Ceiling($days / [double]$ChunkDays)
$parameters = @($config.parameter_codes).Count
$stations = @($config.stations).Count

Write-Host "NRHIS historical USGS archive bootstrap" -ForegroundColor Cyan
Write-Host "  Range:      $StartDate through $EndDate"
Write-Host "  Stations:   $stations"
Write-Host "  Parameters: $parameters"
Write-Host "  Days:       $days"
Write-Host "  Chunk size: $ChunkDays day(s)"
Write-Host "  Requests:   approximately $chunks"
Write-Host "  Output:     $OutputRoot"
Write-Host ""
Write-Host "Build090 checkpoint protection prevents a newer-range checkpoint from silently skipping this older history." -ForegroundColor Green

if ($PlanOnly) {
    Write-Host "PlanOnly selected; no USGS requests were made." -ForegroundColor Yellow
    exit 0
}

$invoke = @{
    StartDate = $StartDate
    EndDate = $EndDate
    ChunkDays = $ChunkDays
    OutputRoot = $OutputRoot
}
if ($NoResume) {
    $invoke.NoResume = $true
}

& $runner @invoke
if ($LASTEXITCODE -ne 0) {
    throw "Historical USGS archive bootstrap failed with exit code $LASTEXITCODE."
}

Write-Host "NRHIS historical USGS archive bootstrap completed." -ForegroundColor Green
