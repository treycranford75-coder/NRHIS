[CmdletBinding()]
param([string]$RepositoryRoot = (Get-Location).Path)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo
$script = Join-Path $repo 'scripts/release/Complete-NrhisAutomatedRelease.ps1'
if (-not (Test-Path $script -PathType Leaf)) { throw "Completion helper not found: $script" }
& $script `
  -BuildNumber '073' `
  -Repository 'treycranford75-coder/NRHIS' `
  -Tag 'v0.1.1-rc73+build073' `
  -ReleaseTitle 'NRHIS Sprint 2 Build073 - Full One-Step Lifecycle' `
  -NotesFile (Join-Path $repo 'docs/releases/BUILD073_RELEASE_NOTES.md') `
  -EvidenceRoot (Join-Path $HOME 'NRHIS-Release-Evidence')
