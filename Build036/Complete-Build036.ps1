[CmdletBinding()]
param(
    [string]$Repository = "treycranford75-coder/NRHIS",
    [string]$ExpectedTag = "v0.1.1-rc36+build036",
    [string]$ReleaseTitle = "NRHIS Sprint 2 Build036 - Automated Publication and Verification RC36",
    [string]$EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence"),
    [string]$ReleaseAsset,
    [switch]$BrowserOnly
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (Get-Location).Path
if (-not (Test-Path (Join-Path $repoRoot ".git"))) { throw "Run from the NRHIS repository root." }
if ((git branch --show-current).Trim() -ne "develop") { throw "Switch to develop after the Build036 PR is merged." }

$automation = Join-Path $repoRoot "scripts\release\Complete-NrhisAutomatedRelease.ps1"
if (-not (Test-Path $automation)) { throw "Missing automation helper: $automation" }

$params = @{
    BuildNumber = "036"
    Repository = $Repository
    Tag = $ExpectedTag
    ReleaseTitle = $ReleaseTitle
    NotesFile = (Join-Path $repoRoot "docs\releases\BUILD036_RELEASE_NOTES.md")
    EvidenceRoot = $EvidenceRoot
}
if ($ReleaseAsset) { $params.ReleaseAsset = $ReleaseAsset }
if ($BrowserOnly) { $params.BrowserOnly = $true }

& $automation @params
