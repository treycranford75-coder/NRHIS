[CmdletBinding()]
param(
    [int]$WaitForMergeMinutes = 20,
    [switch]$BrowserOnly,
    [switch]$NoChain,
    [switch]$NoArchive
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$apply = Join-Path $PSScriptRoot "Apply-Build047.ps1"
if (-not (Test-Path $apply)) { throw "Missing Build047 one-step entry point." }
& $apply -RepositoryRoot (Get-Location).Path -WaitForMergeMinutes $WaitForMergeMinutes -BrowserOnly:$BrowserOnly -NoChain:$NoChain -NoArchive:$NoArchive
