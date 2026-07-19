[CmdletBinding()]
param(
    [int]$WaitForMergeMinutes = 20,
    [switch]$BrowserOnly,
    [switch]$NoChain,
    [switch]$NoArchive
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$apply = Join-Path $PSScriptRoot "Apply-Build050.ps1"
if (-not (Test-Path $apply)) { throw "Missing Build050 one-step entry point." }
$arguments = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $apply,
    "-RepositoryRoot", (Get-Location).Path,
    "-WaitForMergeMinutes", [string]$WaitForMergeMinutes
)
if ($BrowserOnly) { $arguments += "-BrowserOnly" }
if ($NoChain) { $arguments += "-NoChain" }
if ($NoArchive) { $arguments += "-NoArchive" }
& powershell.exe @arguments
if ($LASTEXITCODE -ne 0) { throw "Build050 completion child process failed with exit code $LASTEXITCODE." }
