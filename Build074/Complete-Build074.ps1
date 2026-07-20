[CmdletBinding()]
param([string]$RepositoryRoot = (Get-Location).Path)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo
$script = Join-Path $repo 'scripts/release/Complete-NrhisAutomatedRelease.ps1'
if (-not (Test-Path $script -PathType Leaf)) { throw "Completion helper not found: $script" }
& $script `
  -BuildNumber '074' `
  -Repository 'treycranford75-coder/NRHIS' `
  -Tag 'v0.1.1-rc74+build074' `
  -ReleaseTitle 'NRHIS Sprint 2 Build074 - Resumable Release Lifecycle' `
  -NotesFile (Join-Path $repo 'docs/releases/BUILD074_RELEASE_NOTES.md') `
  -EvidenceRoot (Join-Path $HOME 'NRHIS-Release-Evidence')
