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
    if (-not (Test-Path $migrationScript -PathType Leaf)) { throw "Build055 repository migration helper is missing." }
    & $migrationScript -SourceRepository $repo -DestinationRepository $MigrationDestination -BuildNumber "055" -NoChain:$NoChain
    return
}

$orchestratorSource = Join-Path $payload "scripts\release\Invoke-NrhisOneStepLifecycle.ps1"
if (-not (Test-Path $orchestratorSource)) { throw "Build055 lifecycle helper is missing." }

$asset = Join-Path $repo "NRHIS_Sprint2_Build055_OneStep.zip"
$params = @{
    BuildNumber = "055"
    Repository = "treycranford75-coder/NRHIS"
    Branch = "feature/sprint2-build055"
    CommitMessage = "Build055: add TWDB reservoir operations harvest"
    PullRequestTitle = "Build055: add TWDB reservoir operations harvest"
    PullRequestBodyFile = (Join-Path $payload "docs\releases\BUILD055_PR.md")
    Tag = "v0.1.1-rc55+build055"
    ReleaseTitle = "NRHIS Sprint 2 Build055 - Integrated Basin Operational Snapshot RC54"
    ReleaseNotesFile = (Join-Path $repo "docs\releases\BUILD055_RELEASE_NOTES.md")
    PayloadRoot = $payload
    EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
    WaitForMergeMinutes = $WaitForMergeMinutes
}
if (Test-Path $asset) { $params.ReleaseAsset = $asset }
if ($BrowserOnly) { $params.BrowserOnly = $true }
if ($NoChain) { $params.NoChain = $true }
if ($NoArchive) { $params.NoArchive = $true }

& $orchestratorSource @params
