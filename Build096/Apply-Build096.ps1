[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$payload = Join-Path $PSScriptRoot 'payload'
$baseBranch = 'develop'
$buildNumber = '096'
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
        throw "Build096 payload file is missing: $source"
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
    throw 'Tracked working-tree changes are present. Build096 made no changes.'
}

Invoke-Git @('fetch', 'origin', $baseBranch)
Invoke-Git @('switch', '-C', $featureBranch, "origin/$baseBranch")

$payloadFiles = @(
    'scripts/query_usgs_history.py',
    'scripts/Query-USGS-History.ps1',
    'tests/test_usgs_query_cli_build096.py',
    'docs/Operations/BUILD096_QUERY_CLI_HARDENING.md',
    'docs/releases/BUILD096.md',
    'docs/releases/BUILD096_PR.md',
    'docs/releases/BUILD096_RELEASE_NOTES.md'
)
foreach ($file in $payloadFiles) { Copy-PayloadFile -RelativePath $file }

Write-Host 'Running Build096 focused preflight...' -ForegroundColor Cyan
python -m pytest tests/test_usgs_query_cli_build096.py tests/test_usgs_history_query_build095.py -q
if ($LASTEXITCODE -ne 0) { throw 'Build096 focused deterministic preflight failed.' }

python -m ruff check scripts/query_usgs_history.py tests/test_usgs_query_cli_build096.py
if ($LASTEXITCODE -ne 0) { throw 'Build096 Ruff preflight failed.' }

git diff --check
if ($LASTEXITCODE -ne 0) { throw 'Build096 diff check failed.' }

$runner = Join-Path $repo 'scripts/release/Invoke-NrhisSelfContainedBuild.ps1'
if (-not (Test-Path $runner -PathType Leaf)) { throw "Self-contained lifecycle runner not found: $runner" }

& $runner `
    -BuildNumber $buildNumber `
    -CommitMessage 'Build096: harden finalized historical query CLI' `
    -PullRequestTitle 'Build096: harden finalized historical query CLI' `
    -PullRequestBodyFile (Join-Path $repo 'docs/releases/BUILD096_PR.md') `
    -ReleaseTag 'v0.1.1-build096' `
    -ReleaseTitle 'NRHIS Sprint 2 Build096 - Historical Query CLI Hardening' `
    -ReleaseNotesFile (Join-Path $repo 'docs/releases/BUILD096_RELEASE_NOTES.md') `
    -StagedPaths @(
        'Build096',
        'scripts/query_usgs_history.py',
        'scripts/Query-USGS-History.ps1',
        'tests/test_usgs_query_cli_build096.py',
        'docs/Operations/BUILD096_QUERY_CLI_HARDENING.md',
        'docs/releases/BUILD096.md',
        'docs/releases/BUILD096_PR.md',
        'docs/releases/BUILD096_RELEASE_NOTES.md'
    ) `
    -RepositoryRoot $repo

if ($LASTEXITCODE -ne 0) { throw "Build096 self-contained lifecycle failed with exit code $LASTEXITCODE." }
