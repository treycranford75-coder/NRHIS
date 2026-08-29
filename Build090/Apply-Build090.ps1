[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$payload = Join-Path $PSScriptRoot 'payload'
$baseBranch = 'develop'
$buildNumber = '090'
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
        throw "Build090 payload file is missing: $source"
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
    throw 'Tracked working-tree changes are present. Build090 made no changes.'
}

Invoke-Git @('fetch', 'origin', $baseBranch)
Invoke-Git @('switch', '-C', $featureBranch, "origin/$baseBranch")

$payloadFiles = @(
    'scripts/Bootstrap-USGS-History.ps1',
    'tests/test_usgs_historical_backfill_build090.py',
    'docs/Operations/BUILD090_DEEP_HISTORY_BOOTSTRAP.md',
    'docs/releases/BUILD090.md',
    'docs/releases/BUILD090_PR.md',
    'docs/releases/BUILD090_RELEASE_NOTES.md'
)
foreach ($file in $payloadFiles) {
    Copy-PayloadFile -RelativePath $file
}

$patcher = Join-Path $payload 'scripts/release/patch_build090_historical_backfill.py'
if (-not (Test-Path $patcher -PathType Leaf)) {
    throw "Build090 patcher is missing: $patcher"
}
python $patcher
if ($LASTEXITCODE -ne 0) {
    throw 'Build090 historical backfill patch failed.'
}

Write-Host 'Running Build090 hydrologic preflight...' -ForegroundColor Cyan
python -m ruff check `
    src/nrhis_harvest/usgs_historical_backfill.py `
    tests/test_usgs_historical_backfill_build090.py
if ($LASTEXITCODE -ne 0) {
    throw 'Build090 Ruff preflight failed before commit or push.'
}

python -m pytest tests/test_usgs_historical_backfill_build090.py -q
if ($LASTEXITCODE -ne 0) {
    throw 'Build090 deterministic preflight failed before commit or push.'
}

$releaseHelper = Join-Path $repo 'scripts/release/Invoke-NrhisSelfContainedBuild.ps1'
if (-not (Test-Path $releaseHelper -PathType Leaf)) {
    throw "Build089 self-contained release helper is missing: $releaseHelper"
}

$stagedPaths = @(
    'Build090',
    'src/nrhis_harvest/usgs_historical_backfill.py',
    'scripts/Bootstrap-USGS-History.ps1',
    'tests/test_usgs_historical_backfill_build090.py',
    'docs/Operations/BUILD090_DEEP_HISTORY_BOOTSTRAP.md',
    'docs/releases/BUILD090.md',
    'docs/releases/BUILD090_PR.md',
    'docs/releases/BUILD090_RELEASE_NOTES.md'
)

& $releaseHelper `
    -BuildNumber $buildNumber `
    -CommitMessage 'Build090: enable safe deep-history USGS bootstrap' `
    -PullRequestTitle 'Build090: enable safe deep-history USGS bootstrap' `
    -PullRequestBodyFile (Join-Path $repo 'docs/releases/BUILD090_PR.md') `
    -ReleaseTag 'v0.1.1-build090' `
    -ReleaseTitle 'NRHIS Sprint 2 Build090' `
    -ReleaseNotesFile (Join-Path $repo 'docs/releases/BUILD090_RELEASE_NOTES.md') `
    -RepositoryRoot $repo `
    -BaseBranch $baseBranch `
    -StagedPaths $stagedPaths

if ($LASTEXITCODE -ne 0) {
    throw "Build090 self-contained lifecycle failed with exit code $LASTEXITCODE."
}
