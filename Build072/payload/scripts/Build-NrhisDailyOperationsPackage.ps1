[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [string]$ConfigPath,
    [switch]$AllowUnreleased
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = (Resolve-Path $RepositoryRoot).Path
if (-not $ConfigPath) { $ConfigPath = Join-Path $repo 'config\nrhis\daily_operations_package.json' }
$runner = Join-Path $repo 'scripts\package_daily_operations_report.py'
if (-not (Test-Path $runner -PathType Leaf)) { throw "Daily operations package runner missing: $runner" }
$argsList = @($runner, '--repository-root', $repo, '--config', $ConfigPath)
if ($AllowUnreleased) { $argsList += '--allow-unreleased' }
& python @argsList
if ($LASTEXITCODE -ne 0) { throw "NRHIS daily operations package failed with exit code $LASTEXITCODE." }
