[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path $RepositoryRoot).Path
& (Join-Path $repo 'scripts/release/Complete-NrhisBuild.ps1') `
    -BuildNumber '085' `
    -Tag 'v0.1.1-rc85+build085' `
    -ReleaseTitle 'NRHIS Sprint 2 Build085 - Reservoir Water Budgets' `
    -NotesFile (Join-Path $repo 'docs/releases/BUILD085_RELEASE_NOTES.md') `
    -RepositoryRoot $repo
