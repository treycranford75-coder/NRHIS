[CmdletBinding()]
param(
    [string]$RepositoryRoot,
    [string]$OutputRoot,
    [string]$Period = "P2D",
    [int]$TimeoutSeconds = 30,
    [ValidateRange(1, 6)][int]$MaxAttempts = 3,
    [ValidateRange(1, 120)][int]$InitialBackoffSeconds = 5
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
$RepositoryRoot = (Resolve-Path $RepositoryRoot).Path

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $RepositoryRoot "data\nrhis"
}
$OutputRoot = [System.IO.Path]::GetFullPath($OutputRoot)

$config = Join-Path $RepositoryRoot "config\nrhis\usgs_nueces_basin.json"
$runner = Join-Path $RepositoryRoot "scripts\harvest_usgs_production.py"
if (-not (Test-Path $config -PathType Leaf)) { throw "Missing station configuration: $config" }
if (-not (Test-Path $runner -PathType Leaf)) { throw "Missing Python harvester: $runner" }

for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    & python $runner --config $config --output-root $OutputRoot --period $Period --timeout $TimeoutSeconds
    $code = $LASTEXITCODE
    if ($code -eq 0) { return }
    if ($attempt -ge $MaxAttempts) { break }
    $delay = [Math]::Min($InitialBackoffSeconds * [Math]::Pow(2, $attempt - 1), 120)
    Write-Warning "USGS harvest attempt $attempt failed with exit code $code. Retrying in $delay seconds."
    Start-Sleep -Seconds $delay
}
throw "USGS production harvest failed after $MaxAttempts attempts with exit code $code."
