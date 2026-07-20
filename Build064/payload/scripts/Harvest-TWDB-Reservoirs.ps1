[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [int]$TimeoutSeconds = 60
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
if (-not (Test-Path (Join-Path $repo ".git"))) { throw "Run from the NRHIS repository root." }
Set-Location $repo

$env:PYTHONPATH = (Join-Path $repo "src")
python (Join-Path $repo "scripts\harvest_twdb_reservoirs.py") `
    --config (Join-Path $repo "config\nrhis\twdb_reservoirs_nueces.json") `
    --data-root (Join-Path $repo "data\nrhis") `
    --timeout-seconds $TimeoutSeconds
if ($LASTEXITCODE -ne 0) { throw "TWDB reservoir harvest failed with exit code $LASTEXITCODE" }
