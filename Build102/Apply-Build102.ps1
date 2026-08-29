[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$payload = Join-Path $PSScriptRoot 'payload'
$baseBranch = 'develop'
$buildNumber = '102'
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
        throw "Build102 payload file is missing: $source"
    }
    New-Item -ItemType Directory -Path (Split-Path $destination -Parent) -Force | Out-Null
    Copy-Item -Path $source -Destination $destination -Force
}

Set-Location $repo
if (-not (Test-Path (Join-Path $repo '.git') -PathType Container)) {
    throw "RepositoryRoot is not a Git repository: $repo"
}

$trackedStatus = @(& git status --porcelain --untracked-files=no)
if ($LASTEXITCODE -ne 0) { throw 'Unable to inspect repository status.' }
if ($trackedStatus.Count -gt 0) {
    Write-Host ($trackedStatus -join "`n")
    throw 'Tracked working-tree changes are present. Build102 made no changes.'
}

Invoke-Git @('fetch', 'origin', $baseBranch)
Invoke-Git @('switch', '-C', $featureBranch, "origin/$baseBranch")

$payloadFiles = @(
    'src/nrhis_analysis/lower_nueces_lag_stability.py',
    'scripts/analyze_lower_nueces_lag_stability.py',
    'scripts/Analyze-LowerNueces-LagStability.ps1',
    'tests/test_lower_nueces_lag_stability_build102.py',
    'docs/Operations/BUILD102_LOWER_NUECES_LAG_STABILITY.md',
    'docs/releases/BUILD102.md',
    'docs/releases/BUILD102_PR.md',
    'docs/releases/BUILD102_RELEASE_NOTES.md'
)
foreach ($file in $payloadFiles) { Copy-PayloadFile -RelativePath $file }

Write-Host 'Running Build102 focused preflight...' -ForegroundColor Cyan
python -m pytest tests/test_lower_nueces_lag_stability_build102.py tests/test_lower_nueces_flow_network_build101.py tests/test_usgs_history_query_build095.py -q
if ($LASTEXITCODE -ne 0) { throw 'Build102 focused deterministic preflight failed.' }

python -m ruff check src/nrhis_analysis/lower_nueces_lag_stability.py scripts/analyze_lower_nueces_lag_stability.py tests/test_lower_nueces_lag_stability_build102.py
if ($LASTEXITCODE -ne 0) { throw 'Build102 Ruff preflight failed.' }

git diff --check
if ($LASTEXITCODE -ne 0) { throw 'Build102 diff check failed.' }

$runner = Join-Path $repo 'scripts/release/Invoke-NrhisSelfContainedBuild.ps1'
if (-not (Test-Path $runner -PathType Leaf)) { throw "Self-contained lifecycle runner not found: $runner" }

& $runner `
    -BuildNumber $buildNumber `
    -CommitMessage 'Build102: add lower Nueces lag stability and reach residuals' `
    -PullRequestTitle 'Build102: add lower Nueces lag stability and reach residuals' `
    -PullRequestBodyFile (Join-Path $repo 'docs/releases/BUILD102_PR.md') `
    -ReleaseTag 'v0.1.1-build102' `
    -ReleaseTitle 'NRHIS Sprint 2 Build102 - Lower Nueces Lag Stability and Reach Residuals' `
    -ReleaseNotesFile (Join-Path $repo 'docs/releases/BUILD102_RELEASE_NOTES.md') `
    -StagedPaths @(
        'Build102',
        'src/nrhis_analysis/lower_nueces_lag_stability.py',
        'scripts/analyze_lower_nueces_lag_stability.py',
        'scripts/Analyze-LowerNueces-LagStability.ps1',
        'tests/test_lower_nueces_lag_stability_build102.py',
        'docs/Operations/BUILD102_LOWER_NUECES_LAG_STABILITY.md',
        'docs/releases/BUILD102.md',
        'docs/releases/BUILD102_PR.md',
        'docs/releases/BUILD102_RELEASE_NOTES.md'
    ) `
    -RepositoryRoot $repo
if ($LASTEXITCODE -ne 0) { throw "Build102 self-contained lifecycle failed with exit code $LASTEXITCODE." }
