[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [switch]$BrowserOnly,
    [switch]$NoArchive,
    [switch]$NoChain
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo
$complete = Join-Path $repo "scripts\release\Complete-NrhisAutomatedRelease.ps1"
if (-not (Test-Path $complete -PathType Leaf)) { throw "Completion helper not found: $complete" }
$params = @{
    BuildNumber = "065"
    Repository = "treycranford75-coder/NRHIS"
    Tag = "v0.1.1-rc65+build065"
    ReleaseTitle = "NRHIS Sprint 2 Build065 - Scheduler Installation Hardening"
    NotesFile = (Join-Path $repo "docs\releases\BUILD065_RELEASE_NOTES.md")
    EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
}
$asset = Join-Path $repo "NRHIS_Sprint2_Build065_OneStep.zip"
if (Test-Path $asset) { $params.ReleaseAsset = $asset }
if ($BrowserOnly) { $params.BrowserOnly = $true }
& $complete @params
if (-not $NoArchive) {
    $archive = Join-Path $repo "scripts\release\Archive-NrhisInstallerArtifacts.ps1"
    if (Test-Path $archive -PathType Leaf) {
        & $archive -BuildNumber "065" -RepositoryRoot $repo
    }
}
Write-Host "Build065 completed and verified." -ForegroundColor Green
if (-not $NoChain) {
    Write-Host "lets move on to next build" -ForegroundColor Yellow
    Write-Host "Waiting for Build066 root ZIP." -ForegroundColor Yellow
}
