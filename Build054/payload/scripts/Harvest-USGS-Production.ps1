[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$OutputRoot = (Join-Path $RepositoryRoot "data\nrhis"),
    [string]$Period = "P2D",
    [int]$TimeoutSeconds = 30
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$config = Join-Path $RepositoryRoot "config\nrhis\usgs_nueces_basin.json"
$runner = Join-Path $RepositoryRoot "scripts\harvest_usgs_production.py"
if (-not (Test-Path $config -PathType Leaf)) { throw "Missing station configuration: $config" }
if (-not (Test-Path $runner -PathType Leaf)) { throw "Missing Python harvester: $runner" }

python $runner --config $config --output-root $OutputRoot --period $Period --timeout $TimeoutSeconds
if ($LASTEXITCODE -ne 0) { throw "USGS production harvest failed with exit code $LASTEXITCODE." }
