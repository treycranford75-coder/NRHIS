[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path $RepositoryRoot).Path
& (Join-Path $repo 'scripts/release/Complete-NrhisBuild.ps1') `
    -BuildNumber '087' `
    -Tag 'v0.1.1-rc87+build087' `
    -ReleaseTitle 'NRHIS Sprint 2 Build087 - Structured Lifecycle Contract' `
    -NotesFile (Join-Path $repo 'docs/releases/BUILD087_RELEASE_NOTES.md') `
    -RepositoryRoot $repo
