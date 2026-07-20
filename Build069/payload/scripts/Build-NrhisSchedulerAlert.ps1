[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [string]$ConfigPath,
    [switch]$FailOnAlert
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = (Resolve-Path $RepositoryRoot).Path
if (-not $ConfigPath) { $ConfigPath = Join-Path $repo 'config\nrhis\scheduler_alert.json' }
$runner = Join-Path $repo 'scripts\build_scheduler_alert.py'
if (-not (Test-Path $runner -PathType Leaf)) { throw "Scheduler alert runner missing: $runner" }
$argsList = @($runner, '--repository-root', $repo, '--config', $ConfigPath)
if ($FailOnAlert) { $argsList += '--fail-on-alert' }
& python @argsList
if ($LASTEXITCODE -ne 0) { throw "NRHIS scheduler alert build failed with exit code $LASTEXITCODE." }
