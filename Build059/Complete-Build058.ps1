[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [switch]$NoChain,
    [switch]$NoArchive
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo
$script = Join-Path $repo "scripts\release\Complete-NrhisAutomatedRelease.ps1"
if (-not (Test-Path $script -PathType Leaf)) { throw "Completion helper not found: $script" }
& $script -BuildNumber "058" -Tag "v0.1.1-rc58+build058" -NoChain:$NoChain -NoArchive:$NoArchive
