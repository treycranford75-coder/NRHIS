[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path $RepositoryRoot).Path
& (Join-Path $repo 'scripts/release/Complete-NrhisBuild.ps1') `
    -BuildNumber '086' `
    -Tag 'v0.1.1-rc86+build086' `
    -ReleaseTitle 'NRHIS Sprint 2 Build086 - CI Registration Retry' `
    -NotesFile (Join-Path $repo 'docs/releases/BUILD086_RELEASE_NOTES.md') `
    -RepositoryRoot $repo
