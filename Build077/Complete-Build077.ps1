[CmdletBinding()]
param([string]$RepositoryRoot = (Get-Location).Path)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo
& (Join-Path $repo 'scripts/release/Complete-NrhisBuild.ps1') `
    -BuildNumber '077' `
    -RepositoryRoot $repo `
    -Tag 'v0.1.1-rc77+build077' `
    -ReleaseTitle 'NRHIS Sprint 2 Build077 - Canonical Completion Helper' `
    -NotesFile (Join-Path $repo 'docs/releases/BUILD077_RELEASE_NOTES.md')
