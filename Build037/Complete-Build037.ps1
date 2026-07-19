[CmdletBinding()]
param(
    [int]$WaitForMergeMinutes = 20,
    [switch]$BrowserOnly
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$apply = Join-Path $PSScriptRoot "Apply-Build037.ps1"
if (-not (Test-Path $apply)) { throw "Missing Build037 one-step entry point." }
& $apply -RepositoryRoot (Get-Location).Path -WaitForMergeMinutes $WaitForMergeMinutes -BrowserOnly:$BrowserOnly
