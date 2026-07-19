[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [int]$WaitForMergeMinutes = 20,
    [switch]$BrowserOnly,
    [switch]$NoChain,
    [switch]$NoArchive
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
if (-not (Test-Path (Join-Path $repo ".git"))) { throw "Run from the NRHIS repository root." }
Set-Location $repo

$payload = Join-Path $PSScriptRoot "payload"
$orchestratorSource = Join-Path $payload "scripts\release\Invoke-NrhisOneStepLifecycle.ps1"
if (-not (Test-Path $orchestratorSource)) { throw "Build044 lifecycle helper is missing." }

$asset = Join-Path $repo "NRHIS_Sprint2_Build044_OneStep.zip"
$params = @{
    BuildNumber = "044"
    Repository = "treycranford75-coder/NRHIS"
    Branch = "feature/sprint2-build044"
    CommitMessage = "Build044: replace brittle workflow tests with behavior contracts"
    PullRequestTitle = "Build044: replace brittle workflow tests with behavior contracts"
    PullRequestBodyFile = (Join-Path $payload "docs\releases\BUILD044_PR.md")
    Tag = "v0.1.1-rc44+build044"
    ReleaseTitle = "NRHIS Sprint 2 Build044 - Behavior-Based Workflow Tests RC44"
    ReleaseNotesFile = (Join-Path $repo "docs\releases\BUILD044_RELEASE_NOTES.md")
    PayloadRoot = $payload
    EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
    WaitForMergeMinutes = $WaitForMergeMinutes
}
if (Test-Path $asset) { $params.ReleaseAsset = $asset }
if ($BrowserOnly) { $params.BrowserOnly = $true }
if ($NoChain) { $params.NoChain = $true }
if ($NoArchive) { $params.NoArchive = $true }

& $orchestratorSource @params
