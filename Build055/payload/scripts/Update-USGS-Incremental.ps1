[CmdletBinding()]
param(
    [string]$EndDate = (Get-Date -Format "yyyy-MM-dd"),
    [string]$StudyStart = "2024-02-01",
    [int]$OverlapDays = 2,
    [int]$ChunkDays = 2,
    [int]$LookbackDays = 7,
    [int]$GapMinutes = 120,
    [string]$OutputRoot = "data\nrhis"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$env:PYTHONPATH = (Join-Path $repo "src")
$config = Join-Path $repo "config\nrhis\usgs_nueces_basin.json"
$script = Join-Path $repo "scripts\incremental_usgs_update.py"
$output = Join-Path $repo $OutputRoot
python $script --config $config --output-root $output --end-date $EndDate --study-start $StudyStart --overlap-days $OverlapDays --chunk-days $ChunkDays --lookback-days $LookbackDays --gap-minutes $GapMinutes
if ($LASTEXITCODE -ne 0) { throw "Incremental USGS update failed with exit code $LASTEXITCODE." }
