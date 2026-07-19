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
if (-not (Test-Path $orchestratorSource)) { throw "Build037 lifecycle helper is missing." }

# Use the helper from the ZIP before it is copied into the repository.
$asset = Join-Path $PSScriptRoot "NRHIS_Sprint2_Build037_OneStep.zip"
$params = @{
    BuildNumber = "037"
    Repository = "treycranford75-coder/NRHIS"
    Branch = "feature/sprint2-build037"
    CommitMessage = "Build037: automate the complete build lifecycle from one root ZIP"
    PullRequestTitle = "Build037: automate the complete one-ZIP lifecycle"
    PullRequestBodyFile = (Join-Path $payload "docs\releases\BUILD037_PR.md")
    Tag = "v0.1.1-rc37+build037"
    ReleaseTitle = "NRHIS Sprint 2 Build037 - Complete One-ZIP Lifecycle RC37"
    ReleaseNotesFile = (Join-Path $repo "docs\releases\BUILD037_RELEASE_NOTES.md")
    PayloadRoot = $payload
    EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
    WaitForMergeMinutes = $WaitForMergeMinutes
}
if (Test-Path $asset) { $params.ReleaseAsset = $asset }
if ($BrowserOnly) { $params.BrowserOnly = $true }

& $orchestratorSource @params
