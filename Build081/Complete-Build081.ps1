[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
& (Join-Path $repo 'scripts/release/Complete-NrhisBuild.ps1') `
    -BuildNumber '081' `
    -Tag 'v0.1.1-rc81+build081' `
    -ReleaseTitle 'NRHIS Sprint 2 Build081 - Automatic PR Resolution' `
    -NotesFile (Join-Path $repo 'docs/releases/BUILD081_RELEASE_NOTES.md') `
    -RepositoryRoot $repo
