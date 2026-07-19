[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [int]$WaitForMergeMinutes = 20,
    [switch]$BrowserOnly,
    [switch]$NoChain,
    [switch]$NoArchive,
    [string]$MigrationDestination = "C:\GitHub\NRHIS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
if (-not (Test-Path (Join-Path $repo ".git"))) { throw "Run from the NRHIS repository root." }
Set-Location $repo

$payload = Join-Path $PSScriptRoot "payload"
$migrationScript = Join-Path $payload "scripts\release\Move-NrhisRepositoryOutOfOneDrive.ps1"
if ($repo -match '(?i)[\\/]OneDrive[\\/]') {
    if (-not (Test-Path $migrationScript -PathType Leaf)) { throw "Build051 repository migration helper is missing." }
    & $migrationScript -SourceRepository $repo -DestinationRepository $MigrationDestination -BuildNumber "051" -NoChain:$NoChain
    return
}

$orchestratorSource = Join-Path $payload "scripts\release\Invoke-NrhisOneStepLifecycle.ps1"
if (-not (Test-Path $orchestratorSource)) { throw "Build051 lifecycle helper is missing." }

$asset = Join-Path $repo "NRHIS_Sprint2_Build051_OneStep.zip"
$params = @{
    BuildNumber = "051"
    Repository = "treycranford75-coder/NRHIS"
    Branch = "feature/sprint2-build051"
    CommitMessage = "Build051: add historical USGS Nueces Basin backfill engine"
    PullRequestTitle = "Build051: add historical USGS Nueces Basin backfill engine"
    PullRequestBodyFile = (Join-Path $payload "docs\releases\BUILD051_PR.md")
    Tag = "v0.1.1-rc51+build051"
    ReleaseTitle = "NRHIS Sprint 2 Build051 - Historical USGS Basin Backfill RC51"
    ReleaseNotesFile = (Join-Path $repo "docs\releases\BUILD051_RELEASE_NOTES.md")
    PayloadRoot = $payload
    EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
    WaitForMergeMinutes = $WaitForMergeMinutes
}
if (Test-Path $asset) { $params.ReleaseAsset = $asset }
if ($BrowserOnly) { $params.BrowserOnly = $true }
if ($NoChain) { $params.NoChain = $true }
if ($NoArchive) { $params.NoArchive = $true }

& $orchestratorSource @params
