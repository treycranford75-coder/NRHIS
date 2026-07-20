[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [ValidateRange(0, 2)][int]$QaPassesCompleted = 0,
    [string]$CycleName
)
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo
$argsList = @(
    "scripts/run_operations_cycle.py",
    "--config", "config/nrhis/operations_cycle.json",
    "--repository-root", $repo,
    "--qa-passes-completed", $QaPassesCompleted
)
if ($CycleName) { $argsList += @("--cycle-name", $CycleName) }
& python @argsList
if ($LASTEXITCODE -ne 0) { throw "NRHIS operations cycle failed with exit code $LASTEXITCODE." }
