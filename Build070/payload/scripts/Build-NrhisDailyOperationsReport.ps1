[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [string]$ConfigPath,
    [ValidateRange(0, 10)]
    [int]$QaPassesCompleted = 0,
    [switch]$FailIfHeld
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = (Resolve-Path $RepositoryRoot).Path
if (-not $ConfigPath) { $ConfigPath = Join-Path $repo 'config\nrhis\daily_operations_report.json' }
$runner = Join-Path $repo 'scripts\build_daily_operations_report.py'
if (-not (Test-Path $runner -PathType Leaf)) { throw "Daily operations report runner missing: $runner" }
$argsList = @($runner, '--repository-root', $repo, '--config', $ConfigPath, '--qa-passes-completed', $QaPassesCompleted)
if ($FailIfHeld) { $argsList += '--fail-if-held' }
& python @argsList
if ($LASTEXITCODE -ne 0) { throw "NRHIS daily operations report build failed with exit code $LASTEXITCODE." }
