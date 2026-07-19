[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [int]$WaitForMergeMinutes = 20,
    [switch]$BrowserOnly
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
if (-not (Test-Path (Join-Path $repo ".git"))) { throw "Run from the NRHIS repository root." }
Set-Location $repo

$payload = Join-Path $PSScriptRoot "payload"
$orchestratorSource = Join-Path $payload "scripts\release\Invoke-NrhisOneStepLifecycle.ps1"
if (-not (Test-Path $orchestratorSource)) { throw "Build038 lifecycle helper is missing." }

$asset = Join-Path $PSScriptRoot "NRHIS_Sprint2_Build038_OneStep.zip"
$params = @{
    BuildNumber = "038"
    Repository = "treycranford75-coder/NRHIS"
    Branch = "feature/sprint2-build038"
    CommitMessage = "Build038: authenticate private-repository release verification"
    PullRequestTitle = "Build038: authenticate private-repository release verification"
    PullRequestBodyFile = (Join-Path $payload "docs\releases\BUILD038_PR.md")
    Tag = "v0.1.1-rc38+build038"
    ReleaseTitle = "NRHIS Sprint 2 Build038 - Authenticated Release Verification RC38"
    ReleaseNotesFile = (Join-Path $repo "docs\releases\BUILD038_RELEASE_NOTES.md")
    PayloadRoot = $payload
    EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
    WaitForMergeMinutes = $WaitForMergeMinutes
}
if (Test-Path $asset) { $params.ReleaseAsset = $asset }
if ($BrowserOnly) { $params.BrowserOnly = $true }

& $orchestratorSource @params
