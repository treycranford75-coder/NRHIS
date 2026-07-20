[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$payload = Join-Path $PSScriptRoot 'payload'
$baseBranch = 'develop'
$buildNumber = '089'
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
        throw "Build089 payload file is missing: $source"
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
    throw 'Tracked working-tree changes are present. Build089 made no changes.'
}

Invoke-Git @('fetch', 'origin', $baseBranch)
Invoke-Git @('switch', '-C', $featureBranch, "origin/$baseBranch")

$payloadFiles = @(
    'scripts/release/Invoke-NrhisSelfContainedBuild.ps1',
    'scripts/release/New-NrhisBuildPackage.ps1',
    'tests/test_release_one_step_build089.py',
    'docs/Operations/BUILD089_ONE_STEP_STABILIZATION.md',
    'docs/releases/BUILD089.md',
    'docs/releases/BUILD089_PR.md',
    'docs/releases/BUILD089_RELEASE_NOTES.md'
)

foreach ($file in $payloadFiles) {
    Copy-PayloadFile -RelativePath $file
}

Write-Host 'Running Build089 package preflight...' -ForegroundColor Cyan
python -m ruff check scripts/release tests/test_release_one_step_build089.py
if ($LASTEXITCODE -ne 0) {
    throw 'Build089 Ruff preflight failed before commit or push.'
}

python -m pytest tests/test_release_one_step_build089.py -q
if ($LASTEXITCODE -ne 0) {
    throw 'Build089 deterministic preflight failed before commit or push.'
}

$stagedPaths = @(
    'Build089',
    'scripts/release/Invoke-NrhisSelfContainedBuild.ps1',
    'scripts/release/New-NrhisBuildPackage.ps1',
    'tests/test_release_one_step_build089.py',
    'docs/Operations/BUILD089_ONE_STEP_STABILIZATION.md',
    'docs/releases/BUILD089.md',
    'docs/releases/BUILD089_PR.md',
    'docs/releases/BUILD089_RELEASE_NOTES.md'
)

& (Join-Path $repo 'scripts/release/Invoke-NrhisSelfContainedBuild.ps1') `
    -BuildNumber $buildNumber `
    -CommitMessage 'Build089: stabilize verified one-step release workflow' `
    -PullRequestTitle 'Build089: stabilize verified one-step release workflow' `
    -PullRequestBodyFile (Join-Path $repo 'docs/releases/BUILD089_PR.md') `
    -ReleaseTag 'v0.1.1-build089' `
    -ReleaseTitle 'NRHIS Sprint 2 Build089' `
    -ReleaseNotesFile (Join-Path $repo 'docs/releases/BUILD089_RELEASE_NOTES.md') `
    -RepositoryRoot $repo `
    -BaseBranch $baseBranch `
    -StagedPaths $stagedPaths
