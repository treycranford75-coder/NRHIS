[CmdletBinding()]
param(
    [int]$TimeoutSeconds = 60,
    [string]$OutputRoot = "data\nrhis"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$env:PYTHONPATH = (Join-Path $repo "src")
$config = Join-Path $repo "config\nrhis\nwps_nueces_basin.json"
$script = Join-Path $repo "scripts\harvest_nwps_forecasts.py"
$output = Join-Path $repo $OutputRoot
python $script --config $config --output-root $output --timeout-seconds $TimeoutSeconds
if ($LASTEXITCODE -ne 0) { throw "NWPS forecast harvest failed with exit code $LASTEXITCODE." }
