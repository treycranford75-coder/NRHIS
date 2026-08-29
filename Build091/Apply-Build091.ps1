[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$payload = Join-Path $PSScriptRoot 'payload'
$baseBranch = 'develop'
$buildNumber = '091'
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
        throw "Build091 payload file is missing: $source"
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
    throw 'Tracked working-tree changes are present. Build091 made no changes.'
}

Invoke-Git @('fetch', 'origin', $baseBranch)
Invoke-Git @('switch', '-C', $featureBranch, "origin/$baseBranch")

$payloadFiles = @(
    'scripts/release/New-NrhisCompletionWrapper.ps1',
    'tests/test_release_completion_wrapper_build091.py',
    'docs/Operations/BUILD091_COMPLETION_WRAPPER_CONTRACT.md',
    'docs/releases/BUILD091.md',
    'docs/releases/BUILD091_PR.md',
    'docs/releases/BUILD091_RELEASE_NOTES.md'
)
foreach ($file in $payloadFiles) {
    Copy-PayloadFile -RelativePath $file
}

$patchers = @(
    'scripts/release/patch_build091_self_contained_lifecycle.py',
    'scripts/release/patch_build091_start_self_contained.py'
)
foreach ($relativePatcher in $patchers) {
    $patcher = Join-Path $payload $relativePatcher
    if (-not (Test-Path $patcher -PathType Leaf)) {
        throw "Build091 patcher is missing: $patcher"
    }
    python $patcher
    if ($LASTEXITCODE -ne 0) {
        throw "Build091 patch failed: $relativePatcher"
    }
}

Write-Host 'Running Build091 release-contract preflight...' -ForegroundColor Cyan
python -m ruff check .
if ($LASTEXITCODE -ne 0) {
    throw 'Build091 Ruff preflight failed before commit or push.'
}

python -m pytest -q
if ($LASTEXITCODE -ne 0) {
    throw 'Build091 full deterministic preflight failed before commit or push.'
}

Invoke-Git @('diff', '--check')

$stagedPaths = @(
    'Build091',
    'scripts/release/Invoke-NrhisSelfContainedBuild.ps1',
    'scripts/release/New-NrhisCompletionWrapper.ps1',
    'scripts/release/Start-NrhisBuild.ps1',
    'tests/test_release_completion_wrapper_build091.py',
    'docs/Operations/BUILD091_COMPLETION_WRAPPER_CONTRACT.md',
    'docs/releases/BUILD091.md',
    'docs/releases/BUILD091_PR.md',
    'docs/releases/BUILD091_RELEASE_NOTES.md'
)

Invoke-Git (@('add', '--') + $stagedPaths)
$staged = @(& git diff --cached --name-only)
if ($LASTEXITCODE -ne 0 -or $staged.Count -eq 0) {
    throw 'Build091 produced no staged changes.'
}

Invoke-Git @('-c', 'core.editor=true', 'commit', '-m', 'Build091: make completion wrappers durable')
Invoke-Git @('push', '--force-with-lease', '-u', 'origin', $featureBranch)

Write-Host 'Build091 applied and pushed.' -ForegroundColor Green
