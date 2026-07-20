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
    if (-not (Test-Path $migrationScript -PathType Leaf)) { throw "Build056 repository migration helper is missing." }
    & $migrationScript -SourceRepository $repo -DestinationRepository $MigrationDestination -BuildNumber "056" -NoChain:$NoChain
    return
}

$orchestratorSource = Join-Path $payload "scripts\release\Invoke-NrhisOneStepLifecycle.ps1"
if (-not (Test-Path $orchestratorSource)) { throw "Build056 lifecycle helper is missing." }

$asset = Join-Path $repo "NRHIS_Sprint2_Build056_OneStep.zip"
$params = @{
    BuildNumber = "056"
    Repository = "treycranford75-coder/NRHIS"
    Branch = "feature/sprint2-build056"
    CommitMessage = "Build056: add reservoir evaporation and water budget"
    PullRequestTitle = "Build056: add reservoir evaporation and water budget"
    PullRequestBodyFile = (Join-Path $payload "docs\releases\BUILD056_PR.md")
    Tag = "v0.1.1-rc56+build056"
    ReleaseTitle = "NRHIS Sprint 2 Build056 - Reservoir Evaporation and Water Budget RC56"
    ReleaseNotesFile = (Join-Path $repo "docs\releases\BUILD056_RELEASE_NOTES.md")
    PayloadRoot = $payload
    EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
    WaitForMergeMinutes = $WaitForMergeMinutes
}
if (Test-Path $asset) { $params.ReleaseAsset = $asset }
if ($BrowserOnly) { $params.BrowserOnly = $true }
if ($NoChain) { $params.NoChain = $true }
if ($NoArchive) { $params.NoArchive = $true }

& $orchestratorSource @params
