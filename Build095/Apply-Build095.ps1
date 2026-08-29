[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$payload = Join-Path $PSScriptRoot 'payload'
$baseBranch = 'develop'
$buildNumber = '095'
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
        throw "Build095 payload file is missing: $source"
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
    throw 'Tracked working-tree changes are present. Build095 made no changes.'
}

Invoke-Git @('fetch', 'origin', $baseBranch)
Invoke-Git @('switch', '-C', $featureBranch, "origin/$baseBranch")

$payloadFiles = @(
    'src/nrhis_analysis/__init__.py',
    'src/nrhis_analysis/usgs_history_query.py',
    'scripts/query_usgs_history.py',
    'scripts/Query-USGS-History.ps1',
    'tests/test_usgs_history_query_build095.py',
    'docs/Operations/BUILD095_HISTORICAL_QUERY_ENGINE.md',
    'docs/releases/BUILD095.md',
    'docs/releases/BUILD095_PR.md',
    'docs/releases/BUILD095_RELEASE_NOTES.md'
)
foreach ($file in $payloadFiles) {
    Copy-PayloadFile -RelativePath $file
}

Write-Host 'Running Build095 focused preflight...' -ForegroundColor Cyan
python -m pytest tests/test_usgs_history_query_build095.py -q
if ($LASTEXITCODE -ne 0) {
    throw 'Build095 focused deterministic preflight failed.'
}

git diff --check
if ($LASTEXITCODE -ne 0) {
    throw 'Build095 diff check failed.'
}

$runner = Join-Path $repo 'scripts/release/Invoke-NrhisSelfContainedBuild.ps1'
if (-not (Test-Path $runner -PathType Leaf)) {
    throw "Self-contained lifecycle runner not found: $runner"
}

& $runner `
    -BuildNumber $buildNumber `
    -CommitMessage 'Build095: add finalized historical archive query engine' `
    -PullRequestTitle 'Build095: add finalized historical archive query engine' `
    -PullRequestBodyFile (Join-Path $repo 'docs/releases/BUILD095_PR.md') `
    -ReleaseTag 'v0.1.1-build095' `
    -ReleaseTitle 'NRHIS Sprint 2 Build095 - Historical Query Engine' `
    -ReleaseNotesFile (Join-Path $repo 'docs/releases/BUILD095_RELEASE_NOTES.md') `
    -StagedPaths @(
        'Build095',
        'src/nrhis_analysis/__init__.py',
        'src/nrhis_analysis/usgs_history_query.py',
        'scripts/query_usgs_history.py',
        'scripts/Query-USGS-History.ps1',
        'tests/test_usgs_history_query_build095.py',
        'docs/Operations/BUILD095_HISTORICAL_QUERY_ENGINE.md',
        'docs/releases/BUILD095.md',
        'docs/releases/BUILD095_PR.md',
        'docs/releases/BUILD095_RELEASE_NOTES.md'
    ) `
    -RepositoryRoot $repo

if ($LASTEXITCODE -ne 0) {
    throw "Build095 self-contained lifecycle failed with exit code $LASTEXITCODE."
}
