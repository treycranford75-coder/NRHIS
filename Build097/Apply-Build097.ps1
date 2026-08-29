[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$payload = Join-Path $PSScriptRoot 'payload'
$baseBranch = 'develop'
$buildNumber = '097'
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
        throw "Build097 payload file is missing: $source"
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
    throw 'Tracked working-tree changes are present. Build097 made no changes.'
}

Invoke-Git @('fetch', 'origin', $baseBranch)
Invoke-Git @('switch', '-C', $featureBranch, "origin/$baseBranch")

$payloadFiles = @(
    'src/nrhis_analysis/rincon_flow_analysis.py',
    'scripts/analyze_rincon_flow.py',
    'scripts/Analyze-Rincon-Flow.ps1',
    'tests/test_rincon_flow_analysis_build097.py',
    'docs/Operations/BUILD097_RINCON_FLOW_ANALYSIS.md',
    'docs/releases/BUILD097.md',
    'docs/releases/BUILD097_PR.md',
    'docs/releases/BUILD097_RELEASE_NOTES.md'
)
foreach ($file in $payloadFiles) { Copy-PayloadFile -RelativePath $file }

Write-Host 'Running Build097 focused preflight...' -ForegroundColor Cyan
python -m pytest tests/test_rincon_flow_analysis_build097.py tests/test_usgs_history_query_build095.py -q
if ($LASTEXITCODE -ne 0) { throw 'Build097 focused deterministic preflight failed.' }

python -m ruff check src/nrhis_analysis/rincon_flow_analysis.py scripts/analyze_rincon_flow.py tests/test_rincon_flow_analysis_build097.py
if ($LASTEXITCODE -ne 0) { throw 'Build097 Ruff preflight failed.' }

git diff --check
if ($LASTEXITCODE -ne 0) { throw 'Build097 diff check failed.' }

$runner = Join-Path $repo 'scripts/release/Invoke-NrhisSelfContainedBuild.ps1'
if (-not (Test-Path $runner -PathType Leaf)) { throw "Self-contained lifecycle runner not found: $runner" }

& $runner `
    -BuildNumber $buildNumber `
    -CommitMessage 'Build097: add Rincon discontinuity and directional-flow analysis' `
    -PullRequestTitle 'Build097: add Rincon discontinuity and directional-flow analysis' `
    -PullRequestBodyFile (Join-Path $repo 'docs/releases/BUILD097_PR.md') `
    -ReleaseTag 'v0.1.1-build097' `
    -ReleaseTitle 'NRHIS Sprint 2 Build097 - Rincon Discontinuity and Directional-Flow Analysis' `
    -ReleaseNotesFile (Join-Path $repo 'docs/releases/BUILD097_RELEASE_NOTES.md') `
    -StagedPaths @(
        'Build097',
        'src/nrhis_analysis/rincon_flow_analysis.py',
        'scripts/analyze_rincon_flow.py',
        'scripts/Analyze-Rincon-Flow.ps1',
        'tests/test_rincon_flow_analysis_build097.py',
        'docs/Operations/BUILD097_RINCON_FLOW_ANALYSIS.md',
        'docs/releases/BUILD097.md',
        'docs/releases/BUILD097_PR.md',
        'docs/releases/BUILD097_RELEASE_NOTES.md'
    ) `
    -RepositoryRoot $repo

if ($LASTEXITCODE -ne 0) { throw "Build097 self-contained lifecycle failed with exit code $LASTEXITCODE." }
