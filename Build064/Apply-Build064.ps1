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
    if (-not (Test-Path $migrationScript -PathType Leaf)) { throw "Build064 repository migration helper is missing." }
    & $migrationScript -SourceRepository $repo -DestinationRepository $MigrationDestination -BuildNumber "064" -NoChain:$NoChain
    return
}
$orchestratorSource = Join-Path $payload "scripts\release\Invoke-NrhisOneStepLifecycle.ps1"
if (-not (Test-Path $orchestratorSource -PathType Leaf)) { throw "Build064 lifecycle helper is missing." }
$asset = Join-Path $repo "NRHIS_Sprint2_Build064_OneStep.zip"
$params = @{
    BuildNumber = "064"
    Repository = "treycranford75-coder/NRHIS"
    Branch = "feature/sprint2-build064"
    CommitMessage = "Build064: add twice-daily scheduler and run monitoring"
    PullRequestTitle = "Build064: add twice-daily scheduler and run monitoring"
    PullRequestBodyFile = (Join-Path $payload "docs\releases\BUILD064_PR.md")
    Tag = "v0.1.1-rc64+build064"
    ReleaseTitle = "NRHIS Sprint 2 Build064 - Twice-Daily Scheduler and Run Monitoring"
    ReleaseNotesFile = (Join-Path $payload "docs\releases\BUILD064_RELEASE_NOTES.md")
    PayloadRoot = $payload
    EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
    WaitForMergeMinutes = $WaitForMergeMinutes
}
if (Test-Path $asset) { $params.ReleaseAsset = $asset }
if ($BrowserOnly) { $params.BrowserOnly = $true }
if ($NoChain) { $params.NoChain = $true }
if ($NoArchive) { $params.NoArchive = $true }
& $orchestratorSource @params
