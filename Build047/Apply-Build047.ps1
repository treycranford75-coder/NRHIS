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
if (-not (Test-Path $orchestratorSource)) { throw "Build047 lifecycle helper is missing." }

$asset = Join-Path $repo "NRHIS_Sprint2_Build047_OneStep.zip"
$params = @{
    BuildNumber = "047"
    Repository = "treycranford75-coder/NRHIS"
    Branch = "feature/sprint2-build047"
    CommitMessage = "Build047: add pre-push CI parity gate"
    PullRequestTitle = "Build047: add pre-push CI parity gate"
    PullRequestBodyFile = (Join-Path $payload "docs\releases\BUILD047_PR.md")
    Tag = "v0.1.1-rc46+build047"
    ReleaseTitle = "NRHIS Sprint 2 Build047 - Automated CI Repair Guidance RC46"
    ReleaseNotesFile = (Join-Path $repo "docs\releases\BUILD047_RELEASE_NOTES.md")
    PayloadRoot = $payload
    EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
    WaitForMergeMinutes = $WaitForMergeMinutes
}
if (Test-Path $asset) { $params.ReleaseAsset = $asset }
if ($BrowserOnly) { $params.BrowserOnly = $true }
if ($NoChain) { $params.NoChain = $true }
if ($NoArchive) { $params.NoArchive = $true }

& $orchestratorSource @params
