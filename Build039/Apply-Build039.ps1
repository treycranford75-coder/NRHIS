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
if (-not (Test-Path $orchestratorSource)) { throw "Build039 lifecycle helper is missing." }

$asset = Join-Path $PSScriptRoot "NRHIS_Sprint2_Build039_OneStep.zip"
$params = @{
    BuildNumber = "039"
    Repository = "treycranford75-coder/NRHIS"
    Branch = "feature/sprint2-build039"
    CommitMessage = "Build039: chain verified completion to the next build ZIP"
    PullRequestTitle = "Build039: safely chain verified builds from one-step ZIPs"
    PullRequestBodyFile = (Join-Path $payload "docs\releases\BUILD039_PR.md")
    Tag = "v0.1.1-rc39+build039"
    ReleaseTitle = "NRHIS Sprint 2 Build039 - Safe Build Chaining RC39"
    ReleaseNotesFile = (Join-Path $repo "docs\releases\BUILD039_RELEASE_NOTES.md")
    PayloadRoot = $payload
    EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
    WaitForMergeMinutes = $WaitForMergeMinutes
}
if (Test-Path $asset) { $params.ReleaseAsset = $asset }
if ($BrowserOnly) { $params.BrowserOnly = $true }
if ($NoChain) { $params.NoChain = $true }

& $orchestratorSource @params
