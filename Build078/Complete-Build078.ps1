[CmdletBinding()]
param([string]$RepositoryRoot = (Get-Location).Path)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo
& (Join-Path $repo 'scripts/release/Complete-NrhisBuild.ps1') `
    -BuildNumber '078' `
    -RepositoryRoot $repo `
    -Tag 'v0.1.1-rc78+build078' `
    -ReleaseTitle 'NRHIS Sprint 2 Build078 - Verified Receipt Contract' `
    -NotesFile (Join-Path $repo 'docs/releases/BUILD078_RELEASE_NOTES.md')
