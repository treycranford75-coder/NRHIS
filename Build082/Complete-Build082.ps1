[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path $RepositoryRoot).Path
& (Join-Path $repo 'scripts/release/Complete-NrhisBuild.ps1') `
    -BuildNumber '082' `
    -Tag 'v0.1.1-rc82+build082' `
    -ReleaseTitle 'NRHIS Sprint 2 Build082 - TexasET Regional ET' `
    -NotesFile (Join-Path $repo 'docs/releases/BUILD082_RELEASE_NOTES.md') `
    -RepositoryRoot $repo
