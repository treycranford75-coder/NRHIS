[CmdletBinding()]
param(
    [string]$Config = "config/nrhis/coastal_salt03.json",
    [string]$DataRoot = "data/nrhis"
)
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repo
$env:PYTHONPATH = (Join-Path $repo "src")
python (Join-Path $PSScriptRoot "harvest_salt03_coastal.py") --config $Config --data-root $DataRoot
if ($LASTEXITCODE -ne 0) { throw "SALT03 coastal harvest failed with exit code $LASTEXITCODE" }
