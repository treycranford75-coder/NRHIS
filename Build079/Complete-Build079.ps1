[CmdletBinding()]
param([string]$RepositoryRoot = (Get-Location).Path)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path $RepositoryRoot).Path
& (Join-Path $repo 'scripts/release/Complete-NrhisBuild.ps1') `
    -BuildNumber '079' `
    -RepositoryRoot $repo `
    -Tag 'v0.1.1-rc79+build079' `
    -ReleaseTitle 'NRHIS Sprint 2 Build079 - Null-Safe Release Lifecycle' `
    -NotesFile (Join-Path $repo 'docs/releases/BUILD079_RELEASE_NOTES.md')
if ($LASTEXITCODE -ne 0) { throw 'Build079 completion failed.' }
