[CmdletBinding()]
param(
    [string]$StartDate = "2007-01-01",
    [string]$EndDate = (Get-Date -Format "yyyy-MM-dd"),
    [string]$OutputRoot = (Join-Path (Get-Location).Path "data\nrhis")
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Get-Location).Path
$script = Join-Path $repo "scripts\finalize_usgs_history.py"
if (-not (Test-Path $script -PathType Leaf)) {
    throw "Missing USGS historical finalizer: $script"
}

Write-Host "NRHIS USGS historical archive finalization" -ForegroundColor Cyan
Write-Host "  Range:  $StartDate through $EndDate"
Write-Host "  Output: $OutputRoot"
Write-Host "  Mode:   finalize-only; zero USGS requests" -ForegroundColor Green

$historyPath = Join-Path $OutputRoot "normalized\usgs_historical_observations.jsonl"
if (-not (Test-Path $historyPath -PathType Leaf)) {
    throw "Historical JSONL not found: $historyPath"
}
$historyBytes = (Get-Item $historyPath).Length
$driveRoot = [System.IO.Path]::GetPathRoot((Resolve-Path $OutputRoot).Path)
$driveInfo = [System.IO.DriveInfo]::new($driveRoot)
$recommendedFree = [int64][math]::Max(2GB, $historyBytes * 3)
Write-Host ("  JSONL:  {0:N2} GB" -f ($historyBytes / 1GB))
Write-Host ("  Free:   {0:N2} GB" -f ($driveInfo.AvailableFreeSpace / 1GB))
Write-Host ("  Recommended free working space: {0:N2} GB" -f ($recommendedFree / 1GB))
if ($driveInfo.AvailableFreeSpace -lt $recommendedFree) {
    throw "Insufficient free disk space for bounded-memory external finalization."
}

$env:PYTHONPATH = (Join-Path $repo "src")
& python $script `
    --output-root $OutputRoot `
    --start-date $StartDate `
    --end-date $EndDate

if ($LASTEXITCODE -ne 0) {
    throw "USGS historical archive finalization failed with exit code $LASTEXITCODE."
}
