[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$payload = Join-Path $PSScriptRoot 'payload'
$baseBranch = 'develop'
$buildNumber = '099'
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
        throw "Build099 payload file is missing: $source"
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
    throw 'Tracked working-tree changes are present. Build099 made no changes.'
}

Invoke-Git @('fetch', 'origin', $baseBranch)
Invoke-Git @('switch', '-C', $featureBranch, "origin/$baseBranch")

$payloadFiles = @(
    'src/nrhis_analysis/rincon_evidence_reconciliation.py',
    'scripts/analyze_rincon_evidence_reconciliation.py',
    'scripts/Analyze-Rincon-Evidence.ps1',
    'tests/test_rincon_evidence_reconciliation_build099.py',
    'docs/Operations/BUILD099_RINCON_EVIDENCE_RECONCILIATION.md',
    'docs/releases/BUILD099.md',
    'docs/releases/BUILD099_PR.md',
    'docs/releases/BUILD099_RELEASE_NOTES.md'
)
foreach ($file in $payloadFiles) { Copy-PayloadFile -RelativePath $file }

Write-Host 'Running Build099 focused preflight...' -ForegroundColor Cyan
python -m pytest tests/test_rincon_evidence_reconciliation_build099.py tests/test_rincon_reverse_flow_volume_build098.py tests/test_rincon_flow_analysis_build097.py tests/test_usgs_history_query_build095.py -q
if ($LASTEXITCODE -ne 0) { throw 'Build099 focused deterministic preflight failed.' }

python -m ruff check src/nrhis_analysis/rincon_evidence_reconciliation.py scripts/analyze_rincon_evidence_reconciliation.py tests/test_rincon_evidence_reconciliation_build099.py
if ($LASTEXITCODE -ne 0) { throw 'Build099 Ruff preflight failed.' }

git diff --check
if ($LASTEXITCODE -ne 0) { throw 'Build099 diff check failed.' }

$runner = Join-Path $repo 'scripts/release/Invoke-NrhisSelfContainedBuild.ps1'
if (-not (Test-Path $runner -PathType Leaf)) { throw "Self-contained lifecycle runner not found: $runner" }

& $runner `
    -BuildNumber $buildNumber `
    -CommitMessage 'Build099: reconcile Rincon interval semantics and evidence timeline' `
    -PullRequestTitle 'Build099: reconcile Rincon interval semantics and evidence timeline' `
    -PullRequestBodyFile (Join-Path $repo 'docs/releases/BUILD099_PR.md') `
    -ReleaseTag 'v0.1.1-build099' `
    -ReleaseTitle 'NRHIS Sprint 2 Build099 - Rincon Evidence Reconciliation' `
    -ReleaseNotesFile (Join-Path $repo 'docs/releases/BUILD099_RELEASE_NOTES.md') `
    -StagedPaths @(
        'Build099',
        'src/nrhis_analysis/rincon_evidence_reconciliation.py',
        'scripts/analyze_rincon_evidence_reconciliation.py',
        'scripts/Analyze-Rincon-Evidence.ps1',
        'tests/test_rincon_evidence_reconciliation_build099.py',
        'docs/Operations/BUILD099_RINCON_EVIDENCE_RECONCILIATION.md',
        'docs/releases/BUILD099.md',
        'docs/releases/BUILD099_PR.md',
        'docs/releases/BUILD099_RELEASE_NOTES.md'
    ) `
    -RepositoryRoot $repo
if ($LASTEXITCODE -ne 0) { throw "Build099 self-contained lifecycle failed with exit code $LASTEXITCODE." }
