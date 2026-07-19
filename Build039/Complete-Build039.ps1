[CmdletBinding()]
param(
    [int]$WaitForMergeMinutes = 20,
    [switch]$BrowserOnly,
    [switch]$NoChain
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$apply = Join-Path $PSScriptRoot "Apply-Build039.ps1"
if (-not (Test-Path $apply)) { throw "Missing Build039 one-step entry point." }
& $apply -RepositoryRoot (Get-Location).Path -WaitForMergeMinutes $WaitForMergeMinutes -BrowserOnly:$BrowserOnly -NoChain:$NoChain
