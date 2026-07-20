[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path $RepositoryRoot).Path
& (Join-Path $repo 'scripts/release/Complete-NrhisBuild.ps1') `
    -BuildNumber '083' `
    -Tag 'v0.1.1-rc83+build083' `
    -ReleaseTitle 'NRHIS Sprint 2 Build083 - TexasET Reservoir Evaporation' `
    -NotesFile (Join-Path $repo 'docs/releases/BUILD083_RELEASE_NOTES.md') `
    -RepositoryRoot $repo
