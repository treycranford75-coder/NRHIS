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
    if (-not (Test-Path $migrationScript -PathType Leaf)) { throw "Build063 repository migration helper is missing." }
    & $migrationScript -SourceRepository $repo -DestinationRepository $MigrationDestination -BuildNumber "063" -NoChain:$NoChain
    return
}
$orchestratorSource = Join-Path $payload "scripts\release\Invoke-NrhisOneStepLifecycle.ps1"
if (-not (Test-Path $orchestratorSource -PathType Leaf)) { throw "Build063 lifecycle helper is missing." }
$asset = Join-Path $repo "NRHIS_Sprint2_Build063_OneStep.zip"
$params = @{
    BuildNumber = "063"
    Repository = "treycranford75-coder/NRHIS"
    Branch = "feature/sprint2-build063"
    CommitMessage = "Build063: add operations-cycle reliability hardening and source retry controls"
    PullRequestTitle = "Build063: add operations-cycle reliability hardening and source retry controls"
    PullRequestBodyFile = (Join-Path $payload "docs\releases\BUILD063_PR.md")
    Tag = "v0.1.1-rc63+build063"
    ReleaseTitle = "NRHIS Sprint 2 Build063 - Operations-Cycle Reliability Hardening"
    ReleaseNotesFile = (Join-Path $payload "docs\releases\BUILD063_RELEASE_NOTES.md")
    PayloadRoot = $payload
    EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
    WaitForMergeMinutes = $WaitForMergeMinutes
}
if (Test-Path $asset) { $params.ReleaseAsset = $asset }
if ($BrowserOnly) { $params.BrowserOnly = $true }
if ($NoChain) { $params.NoChain = $true }
if ($NoArchive) { $params.NoArchive = $true }
& $orchestratorSource @params
