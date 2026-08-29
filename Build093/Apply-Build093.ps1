[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$payload = Join-Path $PSScriptRoot 'payload'
$baseBranch = 'develop'
$buildNumber = '093'
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
        throw "Build093 payload file is missing: $source"
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
    throw 'Tracked working-tree changes are present. Build093 made no changes.'
}

Invoke-Git @('fetch', 'origin', $baseBranch)
Invoke-Git @('switch', '-C', $featureBranch, "origin/$baseBranch")

$payloadFiles = @(
    'tests/test_release_installer_archive_guard_build093.py',
    'docs/Operations/BUILD093_INSTALLER_ARCHIVE_GUARD.md',
    'docs/releases/BUILD093.md',
    'docs/releases/BUILD093_PR.md',
    'docs/releases/BUILD093_RELEASE_NOTES.md'
)
foreach ($file in $payloadFiles) {
    Copy-PayloadFile -RelativePath $file
}

$patcher = Join-Path $payload 'scripts/release/patch_build093_installer_archive_guard.py'
if (-not (Test-Path $patcher -PathType Leaf)) {
    throw "Build093 patcher is missing: $patcher"
}
python $patcher
if ($LASTEXITCODE -ne 0) {
    throw 'Build093 installer-archive guard patch failed.'
}

Write-Host 'Running Build093 focused preflight...' -ForegroundColor Cyan
python -m pytest tests/test_release_installer_archive_guard_build093.py -q
if ($LASTEXITCODE -ne 0) {
    throw 'Build093 focused deterministic preflight failed.'
}

git diff --check
if ($LASTEXITCODE -ne 0) {
    throw 'Build093 diff check failed.'
}

$runner = Join-Path $repo 'scripts/release/Invoke-NrhisSelfContainedBuild.ps1'
if (-not (Test-Path $runner -PathType Leaf)) {
    throw "Self-contained lifecycle runner not found: $runner"
}

& $runner `
    -BuildNumber $buildNumber `
    -CommitMessage 'Build093: fix installer archive lifecycle guard' `
    -PullRequestTitle 'Build093: fix installer archive lifecycle guard' `
    -PullRequestBodyFile (Join-Path $repo 'docs/releases/BUILD093_PR.md') `
    -ReleaseTag 'v0.1.1-build093' `
    -ReleaseTitle 'NRHIS Sprint 2 Build093 - Installer Archive Lifecycle Guard' `
    -ReleaseNotesFile (Join-Path $repo 'docs/releases/BUILD093_RELEASE_NOTES.md') `
    -StagedPaths @(
        'Build093',
        'scripts/release/Invoke-NrhisSelfContainedBuild.ps1',
        'tests/test_release_installer_archive_guard_build093.py',
        'docs/Operations/BUILD093_INSTALLER_ARCHIVE_GUARD.md',
        'docs/releases/BUILD093.md',
        'docs/releases/BUILD093_PR.md',
        'docs/releases/BUILD093_RELEASE_NOTES.md'
    ) `
    -RepositoryRoot $repo

if ($LASTEXITCODE -ne 0) {
    throw "Build093 self-contained lifecycle failed with exit code $LASTEXITCODE."
}
