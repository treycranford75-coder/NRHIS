[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^\d{3}$')][string]$BuildNumber,
    [string]$RepositoryRoot = (Get-Location).Path,
    [string]$PullRequestUrl,
    [string]$BaseBranch = 'develop',
    [switch]$SkipArchive
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'GitHub CLI (gh) is required to resume the release lifecycle.'
}

& gh auth status 1>$null 2>$null
if ($LASTEXITCODE -ne 0) {
    throw 'GitHub CLI is not authenticated. Run: gh auth login'
}

$featureBranch = "feature/sprint2-build$BuildNumber"
if ([string]::IsNullOrWhiteSpace($PullRequestUrl)) {
    $PullRequestUrl = (& gh pr list `
        --head $featureBranch `
        --base $BaseBranch `
        --state all `
        --json url `
        --jq '.[0].url').Trim()

    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($PullRequestUrl)) {
        throw "No pull request found for $featureBranch into $BaseBranch."
    }
}

$lifecycle = Join-Path $repo 'scripts\release\Finish-NrhisBuildLifecycle.ps1'
if (-not (Test-Path $lifecycle -PathType Leaf)) {
    throw "Lifecycle helper not found: $lifecycle"
}

$statePath = Join-Path $HOME "NRHIS-Release-Evidence\Build$BuildNumber\lifecycle-state.json"
if (Test-Path $statePath -PathType Leaf) {
    $priorState = Get-Content $statePath -Raw | ConvertFrom-Json
    Write-Host "Prior lifecycle state: $($priorState.phase) / $($priorState.status)" -ForegroundColor DarkGray
}

Write-Host "Resuming Build$BuildNumber lifecycle from $PullRequestUrl" -ForegroundColor Cyan
& $lifecycle `
    -BuildNumber $BuildNumber `
    -PullRequestUrl $PullRequestUrl `
    -RepositoryRoot $repo `
    -BaseBranch $BaseBranch `
    -SkipArchive:$SkipArchive

if ($LASTEXITCODE -ne 0) {
    throw "Build$BuildNumber resumed lifecycle failed with exit code $LASTEXITCODE."
}
