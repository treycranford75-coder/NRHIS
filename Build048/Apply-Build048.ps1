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
if (-not (Test-Path $orchestratorSource)) { throw "Build048 lifecycle helper is missing." }

$asset = Join-Path $repo "NRHIS_Sprint2_Build048_OneStep.zip"
$params = @{
    BuildNumber = "048"
    Repository = "treycranford75-coder/NRHIS"
    Branch = "feature/sprint2-build048"
    CommitMessage = "Build048: add workflow contract preflight gate"
    PullRequestTitle = "Build048: add workflow contract preflight gate"
    PullRequestBodyFile = (Join-Path $payload "docs\releases\BUILD048_PR.md")
    Tag = "v0.1.1-rc48+build048"
    ReleaseTitle = "NRHIS Sprint 2 Build048 - Workflow Contract Preflight RC48"
    ReleaseNotesFile = (Join-Path $repo "docs\releases\BUILD048_RELEASE_NOTES.md")
    PayloadRoot = $payload
    EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
    WaitForMergeMinutes = $WaitForMergeMinutes
}
if (Test-Path $asset) { $params.ReleaseAsset = $asset }
if ($BrowserOnly) { $params.BrowserOnly = $true }
if ($NoChain) { $params.NoChain = $true }
if ($NoArchive) { $params.NoArchive = $true }

& $orchestratorSource @params
