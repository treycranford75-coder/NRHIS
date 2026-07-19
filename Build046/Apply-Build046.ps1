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
if (-not (Test-Path $orchestratorSource)) { throw "Build046 lifecycle helper is missing." }

$asset = Join-Path $repo "NRHIS_Sprint2_Build046_OneStep.zip"
$params = @{
    BuildNumber = "046"
    Repository = "treycranford75-coder/NRHIS"
    Branch = "feature/sprint2-build046"
    CommitMessage = "Build046: generate automatic CI repair guidance"
    PullRequestTitle = "Build046: generate automatic CI repair guidance"
    PullRequestBodyFile = (Join-Path $payload "docs\releases\BUILD046_PR.md")
    Tag = "v0.1.1-rc46+build046"
    ReleaseTitle = "NRHIS Sprint 2 Build046 - Automated CI Repair Guidance RC46"
    ReleaseNotesFile = (Join-Path $repo "docs\releases\BUILD046_RELEASE_NOTES.md")
    PayloadRoot = $payload
    EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
    WaitForMergeMinutes = $WaitForMergeMinutes
}
if (Test-Path $asset) { $params.ReleaseAsset = $asset }
if ($BrowserOnly) { $params.BrowserOnly = $true }
if ($NoChain) { $params.NoChain = $true }
if ($NoArchive) { $params.NoArchive = $true }

& $orchestratorSource @params
