[CmdletBinding()]
param([string]$RepositoryRoot = (Get-Location).Path)
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo
$script = Join-Path $repo "scripts\release\Complete-NrhisAutomatedRelease.ps1"
if (-not (Test-Path $script -PathType Leaf)) { throw "Completion helper not found: $script" }
& $script `
    -BuildNumber "066" `
    -Repository "treycranford75-coder/NRHIS" `
    -Tag "v0.1.1-rc66+build066" `
    -ReleaseTitle "NRHIS Sprint 2 Build066 - Scheduler Health Monitoring" `
    -NotesFile (Join-Path $repo "docs\releases\BUILD066_RELEASE_NOTES.md") `
    -EvidenceRoot (Join-Path $HOME "NRHIS-Release-Evidence")
