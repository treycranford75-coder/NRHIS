[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$payload = Join-Path $PSScriptRoot 'payload'
$baseBranch = 'develop'
$buildNumber = '092'
$featureBranch = "feature/sprint2-build$buildNumber"

function Invoke-Git {
    param([Parameter(Mandatory)][string[]]$Arguments)
    & git @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Arguments -join ' ') failed with exit code $LASTEXITCODE."
    }
}

function Copy-PayloadFile {
    param([Parameter(Mandatory)][string]$RelativePath)
    $source = Join-Path $payload $RelativePath
    $destination = Join-Path $repo $RelativePath
    if (-not (Test-Path $source -PathType Leaf)) {
        throw "Build092 payload file is missing: $source"
    }
    New-Item -ItemType Directory -Path (Split-Path $destination -Parent) -Force | Out-Null
    Copy-Item -Path $source -Destination $destination -Force
}

Set-Location $repo
if (-not (Test-Path (Join-Path $repo '.git') -PathType Container)) {
    throw "RepositoryRoot is not a Git repository: $repo"
}

$trackedStatus = @(& git status --porcelain --untracked-files=no)
if ($LASTEXITCODE -ne 0) {
    throw 'Unable to inspect repository status.'
}
if ($trackedStatus.Count -gt 0) {
    Write-Host ($trackedStatus -join "`n")
    throw 'Tracked working-tree changes are present. Build092 made no changes.'
}

Invoke-Git @('fetch', 'origin', $baseBranch)
Invoke-Git @('switch', '-C', $featureBranch, "origin/$baseBranch")

$payloadFiles = @(
    'tests/test_usgs_deep_history_build092.py',
    'docs/Operations/BUILD092_DEEP_HISTORY_HARDENING.md',
    'docs/releases/BUILD092.md',
    'docs/releases/BUILD092_PR.md',
    'docs/releases/BUILD092_RELEASE_NOTES.md'
)
foreach ($file in $payloadFiles) {
    Copy-PayloadFile -RelativePath $file
}

$patcher = Join-Path $payload 'scripts/release/patch_build092_usgs_deep_history.py'
if (-not (Test-Path $patcher -PathType Leaf)) {
    throw "Build092 patcher is missing: $patcher"
}
python $patcher
if ($LASTEXITCODE -ne 0) {
    throw 'Build092 USGS deep-history patch failed.'
}

Write-Host 'Running Build092 focused preflight...' -ForegroundColor Cyan
python -m pytest tests/test_usgs_deep_history_build092.py -q
if ($LASTEXITCODE -ne 0) {
    throw 'Build092 focused deterministic preflight failed.'
}

git diff --check
if ($LASTEXITCODE -ne 0) {
    throw 'Build092 diff check failed.'
}

$runner = Join-Path $repo 'scripts/release/Invoke-NrhisSelfContainedBuild.ps1'
if (-not (Test-Path $runner -PathType Leaf)) {
    throw "Self-contained lifecycle runner not found: $runner"
}

& $runner `
    -BuildNumber $buildNumber `
    -CommitMessage 'Build092: harden USGS deep-history evidence and scale' `
    -PullRequestTitle 'Build092: harden USGS deep-history evidence and scale' `
    -PullRequestBodyFile (Join-Path $repo 'docs/releases/BUILD092_PR.md') `
    -ReleaseTag 'v0.1.1-build092' `
    -ReleaseTitle 'NRHIS Sprint 2 Build092 - USGS Deep-History Evidence and Scale Hardening' `
    -ReleaseNotesFile (Join-Path $repo 'docs/releases/BUILD092_RELEASE_NOTES.md') `
    -StagedPaths @(
        'Build092',
        'src/nrhis_harvest/usgs_historical_backfill.py',
        'config/nrhis/usgs_nueces_basin.json',
        'scripts/Bootstrap-USGS-History.ps1',
        'tests/test_usgs_deep_history_build092.py',
        'docs/Operations/BUILD092_DEEP_HISTORY_HARDENING.md',
        'docs/releases/BUILD092.md',
        'docs/releases/BUILD092_PR.md',
        'docs/releases/BUILD092_RELEASE_NOTES.md'
    ) `
    -RepositoryRoot $repo

if ($LASTEXITCODE -ne 0) {
    throw "Build092 self-contained lifecycle failed with exit code $LASTEXITCODE."
}
