[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path $RepositoryRoot).Path
& (Join-Path $repo 'scripts/release/Complete-NrhisBuild.ps1') `
    -BuildNumber '084' `
    -Tag 'v0.1.1-rc84+build084' `
    -ReleaseTitle 'NRHIS Sprint 2 Build084 - Reservoir Evaporation Rollups' `
    -NotesFile (Join-Path $repo 'docs/releases/BUILD084_RELEASE_NOTES.md') `
    -RepositoryRoot $repo
