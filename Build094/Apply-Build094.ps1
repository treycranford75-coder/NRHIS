[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$payload = Join-Path $PSScriptRoot 'payload'
$baseBranch = 'develop'
$buildNumber = '094'
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
        throw "Build094 payload file is missing: $source"
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
    throw 'Tracked working-tree changes are present. Build094 made no changes.'
}

Invoke-Git @('fetch', 'origin', $baseBranch)
Invoke-Git @('switch', '-C', $featureBranch, "origin/$baseBranch")

$payloadFiles = @(
    'scripts/finalize_usgs_history.py',
    'scripts/Finalize-USGS-History.ps1',
    'tests/test_usgs_large_archive_finalization_build094.py',
    'docs/Operations/BUILD094_LARGE_ARCHIVE_FINALIZATION.md',
    'docs/releases/BUILD094.md',
    'docs/releases/BUILD094_PR.md',
    'docs/releases/BUILD094_RELEASE_NOTES.md'
)
foreach ($file in $payloadFiles) {
    Copy-PayloadFile -RelativePath $file
}

$patcher = Join-Path $payload 'scripts/release/patch_build094_large_archive_finalization.py'
if (-not (Test-Path $patcher -PathType Leaf)) {
    throw "Build094 patcher is missing: $patcher"
}
python $patcher
if ($LASTEXITCODE -ne 0) {
    throw 'Build094 large-archive patch failed.'
}

Write-Host 'Running Build094 focused preflight...' -ForegroundColor Cyan
python -m pytest tests/test_usgs_large_archive_finalization_build094.py -q
if ($LASTEXITCODE -ne 0) {
    throw 'Build094 focused deterministic preflight failed.'
}

git diff --check
if ($LASTEXITCODE -ne 0) {
    throw 'Build094 diff check failed.'
}

$runner = Join-Path $repo 'scripts/release/Invoke-NrhisSelfContainedBuild.ps1'
if (-not (Test-Path $runner -PathType Leaf)) {
    throw "Self-contained lifecycle runner not found: $runner"
}

& $runner `
    -BuildNumber $buildNumber `
    -CommitMessage 'Build094: add bounded-memory historical finalization' `
    -PullRequestTitle 'Build094: add bounded-memory historical finalization' `
    -PullRequestBodyFile (Join-Path $repo 'docs/releases/BUILD094_PR.md') `
    -ReleaseTag 'v0.1.1-build094' `
    -ReleaseTitle 'NRHIS Sprint 2 Build094 - Large-Archive Finalization' `
    -ReleaseNotesFile (Join-Path $repo 'docs/releases/BUILD094_RELEASE_NOTES.md') `
    -StagedPaths @(
        'Build094',
        'src/nrhis_harvest/usgs_historical_backfill.py',
        'scripts/finalize_usgs_history.py',
        'scripts/Finalize-USGS-History.ps1',
        'tests/test_usgs_large_archive_finalization_build094.py',
        'docs/Operations/BUILD094_LARGE_ARCHIVE_FINALIZATION.md',
        'docs/releases/BUILD094.md',
        'docs/releases/BUILD094_PR.md',
        'docs/releases/BUILD094_RELEASE_NOTES.md'
    ) `
    -RepositoryRoot $repo

if ($LASTEXITCODE -ne 0) {
    throw "Build094 self-contained lifecycle failed with exit code $LASTEXITCODE."
}
