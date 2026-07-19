[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [int]$WaitForMergeMinutes = 20,
    [switch]$BrowserOnly,
    [switch]$NoChain
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
if (-not (Test-Path (Join-Path $repo ".git"))) { throw "Run from the NRHIS repository root." }
Set-Location $repo

$payload = Join-Path $PSScriptRoot "payload"
$orchestratorSource = Join-Path $payload "scripts\release\Invoke-NrhisOneStepLifecycle.ps1"
if (-not (Test-Path $orchestratorSource)) { throw "Build040 lifecycle helper is missing." }

$asset = Join-Path $repo "NRHIS_Sprint2_Build040_OneStep.zip"
$params = @{
    BuildNumber = "040"
    Repository = "treycranford75-coder/NRHIS"
    Branch = "feature/sprint2-build040"
    CommitMessage = "Build040: harden package discovery and resumable extraction"
    PullRequestTitle = "Build040: remove remaining one-step lifecycle friction"
    PullRequestBodyFile = (Join-Path $payload "docs\releases\BUILD040_PR.md")
    Tag = "v0.1.1-rc40+build040"
    ReleaseTitle = "NRHIS Sprint 2 Build040 - Resumable Package Discovery RC40"
    ReleaseNotesFile = (Join-Path $repo "docs\releases\BUILD040_RELEASE_NOTES.md")
    PayloadRoot = $payload
    EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
    WaitForMergeMinutes = $WaitForMergeMinutes
}
if (Test-Path $asset) { $params.ReleaseAsset = $asset }
if ($BrowserOnly) { $params.BrowserOnly = $true }
if ($NoChain) { $params.NoChain = $true }

& $orchestratorSource @params
