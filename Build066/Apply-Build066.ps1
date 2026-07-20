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
$orchestratorSource = Join-Path $payload "scripts\release\Invoke-NrhisOneStepLifecycle.ps1"
if (-not (Test-Path $orchestratorSource)) {
    $orchestratorSource = Join-Path $repo "scripts\release\Invoke-NrhisOneStepLifecycle.ps1"
}
if (-not (Test-Path $orchestratorSource)) { throw "Build066 lifecycle helper is missing." }
$asset = Join-Path $repo "NRHIS_Sprint2_Build066_OneStep.zip"
$params = @{
    BuildNumber = "066"
    Repository = "treycranford75-coder/NRHIS"
    Branch = "feature/sprint2-build066"
    CommitMessage = "Build066: add scheduler health monitoring and missed-run detection"
    PullRequestTitle = "Build066: add scheduler health monitoring and missed-run detection"
    PullRequestBodyFile = (Join-Path $payload "docs\releases\BUILD066_PR.md")
    Tag = "v0.1.1-rc66+build066"
    ReleaseTitle = "NRHIS Sprint 2 Build066 - Scheduler Health Monitoring"
    ReleaseNotesFile = (Join-Path $payload "docs\releases\BUILD066_RELEASE_NOTES.md")
    PayloadRoot = $payload
    EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
    WaitForMergeMinutes = $WaitForMergeMinutes
}
if (Test-Path $asset) { $params.ReleaseAsset = $asset }
if ($BrowserOnly) { $params.BrowserOnly = $true }
if ($NoChain) { $params.NoChain = $true }
if ($NoArchive) { $params.NoArchive = $true }
& $orchestratorSource @params
