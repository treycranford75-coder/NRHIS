[CmdletBinding()]
param([string]$RepositoryRoot = (Get-Location).Path)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo
$script = Join-Path $repo 'scripts/release/Complete-NrhisAutomatedRelease.ps1'
if (-not (Test-Path $script -PathType Leaf)) { throw "Completion helper not found: $script" }
& $script `
  -BuildNumber '070' `
  -Repository 'treycranford75-coder/NRHIS' `
  -Tag 'v0.1.1-rc70+build070' `
  -ReleaseTitle 'NRHIS Sprint 2 Build070 - Daily Operations Report Publisher' `
  -NotesFile (Join-Path $repo 'docs/releases/BUILD070_RELEASE_NOTES.md') `
  -EvidenceRoot (Join-Path $HOME 'NRHIS-Release-Evidence')
