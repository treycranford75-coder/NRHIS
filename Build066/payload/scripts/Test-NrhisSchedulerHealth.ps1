[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [string]$ConfigPath,
    [switch]$FailOnUnhealthy
)
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path $RepositoryRoot).Path
if (-not $ConfigPath) { $ConfigPath = Join-Path $repo "config\nrhis\scheduler_health.json" }
$runner = Join-Path $repo "scripts\test_nrhis_scheduler_health.py"
if (-not (Test-Path $runner -PathType Leaf)) { throw "Scheduler health runner missing: $runner" }
$argsList = @($runner, "--repository-root", $repo, "--config", $ConfigPath)
if ($FailOnUnhealthy) { $argsList += "--fail-on-unhealthy" }
& python @argsList
if ($LASTEXITCODE -ne 0) { throw "NRHIS scheduler health check failed with exit code $LASTEXITCODE." }
