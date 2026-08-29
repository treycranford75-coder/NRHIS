[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$payload = Join-Path $PSScriptRoot 'payload'
$baseBranch = 'develop'
$buildNumber = '098'
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
        throw "Build098 payload file is missing: $source"
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
    throw 'Tracked working-tree changes are present. Build098 made no changes.'
}

Invoke-Git @('fetch', 'origin', $baseBranch)
Invoke-Git @('switch', '-C', $featureBranch, "origin/$baseBranch")

$payloadFiles = @(
    'src/nrhis_analysis/rincon_reverse_flow_volume.py',
    'scripts/analyze_rincon_reverse_flow.py',
    'scripts/Analyze-Rincon-ReverseFlow.ps1',
    'tests/test_rincon_reverse_flow_volume_build098.py',
    'docs/Operations/BUILD098_RINCON_REVERSE_FLOW_VOLUME.md',
    'docs/releases/BUILD098.md',
    'docs/releases/BUILD098_PR.md',
    'docs/releases/BUILD098_RELEASE_NOTES.md'
)
foreach ($file in $payloadFiles) { Copy-PayloadFile -RelativePath $file }

Write-Host 'Running Build098 focused preflight...' -ForegroundColor Cyan
python -m pytest tests/test_rincon_reverse_flow_volume_build098.py tests/test_rincon_flow_analysis_build097.py tests/test_usgs_history_query_build095.py -q
if ($LASTEXITCODE -ne 0) { throw 'Build098 focused deterministic preflight failed.' }

python -m ruff check src/nrhis_analysis/rincon_reverse_flow_volume.py scripts/analyze_rincon_reverse_flow.py tests/test_rincon_reverse_flow_volume_build098.py
if ($LASTEXITCODE -ne 0) { throw 'Build098 Ruff preflight failed.' }

git diff --check
if ($LASTEXITCODE -ne 0) { throw 'Build098 diff check failed.' }

$runner = Join-Path $repo 'scripts/release/Invoke-NrhisSelfContainedBuild.ps1'
if (-not (Test-Path $runner -PathType Leaf)) { throw "Self-contained lifecycle runner not found: $runner" }
& $runner `
    -BuildNumber $buildNumber `
    -CommitMessage 'Build098: add evidence-grade Rincon reverse-flow volume analysis' `
    -PullRequestTitle 'Build098: add evidence-grade Rincon reverse-flow volume analysis' `
    -PullRequestBodyFile (Join-Path $repo 'docs/releases/BUILD098_PR.md') `
    -ReleaseTag 'v0.1.1-build098' `
    -ReleaseTitle 'NRHIS Sprint 2 Build098 - Rincon Reverse-Flow Volume Analysis' `
    -ReleaseNotesFile (Join-Path $repo 'docs/releases/BUILD098_RELEASE_NOTES.md') `
    -StagedPaths @(
        'Build098',
        'src/nrhis_analysis/rincon_reverse_flow_volume.py',
        'scripts/analyze_rincon_reverse_flow.py',
        'scripts/Analyze-Rincon-ReverseFlow.ps1',
        'tests/test_rincon_reverse_flow_volume_build098.py',
        'docs/Operations/BUILD098_RINCON_REVERSE_FLOW_VOLUME.md',
        'docs/releases/BUILD098.md',
        'docs/releases/BUILD098_PR.md',
        'docs/releases/BUILD098_RELEASE_NOTES.md'
    ) `
    -RepositoryRoot $repo
if ($LASTEXITCODE -ne 0) { throw "Build098 self-contained lifecycle failed with exit code $LASTEXITCODE." }
