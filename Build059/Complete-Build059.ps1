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
& $script `
    -BuildNumber "059" `
    -Repository "treycranford75-coder/NRHIS" `
    -Tag "v0.1.1-rc59+build059" `
    -ReleaseTitle "NRHIS Sprint 2 Build059 - SALT03 Coastal Water-Quality Harvest" `
    -NotesFile (Join-Path $repo "docs\releases\BUILD059_RELEASE_NOTES.md") `
    -EvidenceRoot (Join-Path $HOME "NRHIS-Release-Evidence")
