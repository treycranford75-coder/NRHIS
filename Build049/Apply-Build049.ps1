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
    if (-not (Test-Path $migrationScript -PathType Leaf)) { throw "Build049 repository migration helper is missing." }
    & $migrationScript -SourceRepository $repo -DestinationRepository $MigrationDestination -BuildNumber "049" -NoChain:$NoChain
    return
}

$orchestratorSource = Join-Path $payload "scripts\release\Invoke-NrhisOneStepLifecycle.ps1"
if (-not (Test-Path $orchestratorSource)) { throw "Build049 lifecycle helper is missing." }

$asset = Join-Path $repo "NRHIS_Sprint2_Build049_OneStep.zip"
$params = @{
    BuildNumber = "049"
    Repository = "treycranford75-coder/NRHIS"
    Branch = "feature/sprint2-build049"
    CommitMessage = "Build049: migrate lifecycle execution outside OneDrive"
    PullRequestTitle = "Build049: migrate lifecycle execution outside OneDrive"
    PullRequestBodyFile = (Join-Path $payload "docs\releases\BUILD049_PR.md")
    Tag = "v0.1.1-rc49+build049"
    ReleaseTitle = "NRHIS Sprint 2 Build049 - Repository Location Safety RC49"
    ReleaseNotesFile = (Join-Path $repo "docs\releases\BUILD049_RELEASE_NOTES.md")
    PayloadRoot = $payload
    EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
    WaitForMergeMinutes = $WaitForMergeMinutes
}
if (Test-Path $asset) { $params.ReleaseAsset = $asset }
if ($BrowserOnly) { $params.BrowserOnly = $true }
if ($NoChain) { $params.NoChain = $true }
if ($NoArchive) { $params.NoArchive = $true }

& $orchestratorSource @params
