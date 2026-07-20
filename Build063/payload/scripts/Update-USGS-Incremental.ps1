[CmdletBinding()]
param(
    [string]$RepositoryRoot,
    [string]$EndDate = (Get-Date -Format "yyyy-MM-dd"),
    [string]$StudyStart = (Get-Date).AddDays(-2).ToString("yyyy-MM-dd"),
    [int]$OverlapDays = 2,
    [int]$ChunkDays = 2,
    [int]$LookbackDays = 7,
    [int]$GapMinutes = 120,
    [string]$OutputRoot
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) {
        $RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    }
    else {
        $RepositoryRoot = (Get-Location).Path
    }
}
$repo = (Resolve-Path $RepositoryRoot).Path
if ([string]::IsNullOrWhiteSpace($OutputRoot)) { $OutputRoot = Join-Path $repo "data\nrhis" }
elseif (-not [System.IO.Path]::IsPathRooted($OutputRoot)) { $OutputRoot = Join-Path $repo $OutputRoot }
$OutputRoot = [System.IO.Path]::GetFullPath($OutputRoot)

$env:PYTHONPATH = (Join-Path $repo "src")
$config = Join-Path $repo "config\nrhis\usgs_nueces_basin.json"
$script = Join-Path $repo "scripts\incremental_usgs_update.py"
& python $script --config $config --output-root $OutputRoot --end-date $EndDate --study-start $StudyStart --overlap-days $OverlapDays --chunk-days $ChunkDays --lookback-days $LookbackDays --gap-minutes $GapMinutes
if ($LASTEXITCODE -ne 0) { throw "Incremental USGS update failed with exit code $LASTEXITCODE." }
