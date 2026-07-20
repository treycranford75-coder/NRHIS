[CmdletBinding()]
param([string]$RepositoryRoot = (Get-Location).Path)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path $RepositoryRoot).Path
$helper = Join-Path $repo 'scripts/release/Complete-NrhisBuild.ps1'
if (-not (Test-Path $helper -PathType Leaf)) { throw "Completion helper not found: $helper" }
& $helper `
    -BuildNumber '080' `
    -RepositoryRoot $repo `
    -Tag 'v0.1.1-rc80+build080' `
    -ReleaseTitle 'NRHIS Sprint 2 Build080 - Release Lifecycle Preflight' `
    -NotesFile (Join-Path $repo 'docs/releases/BUILD080_RELEASE_NOTES.md')
if ($LASTEXITCODE -ne 0) { throw 'Build080 completion failed.' }
