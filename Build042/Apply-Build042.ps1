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
if (-not (Test-Path $orchestratorSource)) { throw "Build042 lifecycle helper is missing." }

$asset = Join-Path $repo "NRHIS_Sprint2_Build042_OneStep.zip"
$params = @{
    BuildNumber = "042"
    Repository = "treycranford75-coder/NRHIS"
    Branch = "feature/sprint2-build042"
    CommitMessage = "Build042: skip locked directory deletion retries noninteractively"
    PullRequestTitle = "Build042: skip locked directory deletion retries noninteractively"
    PullRequestBodyFile = (Join-Path $payload "docs\releases\BUILD042_PR.md")
    Tag = "v0.1.1-rc42+build042"
    ReleaseTitle = "NRHIS Sprint 2 Build042 - Noninteractive Windows Deletion Handling RC42"
    ReleaseNotesFile = (Join-Path $repo "docs\releases\BUILD042_RELEASE_NOTES.md")
    PayloadRoot = $payload
    EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
    WaitForMergeMinutes = $WaitForMergeMinutes
}
if (Test-Path $asset) { $params.ReleaseAsset = $asset }
if ($BrowserOnly) { $params.BrowserOnly = $true }
if ($NoChain) { $params.NoChain = $true }
if ($NoArchive) { $params.NoArchive = $true }

& $orchestratorSource @params
