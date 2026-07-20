[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = (Resolve-Path $RepositoryRoot).Path
$payload = Join-Path $PSScriptRoot 'payload'

function Copy-PayloadFile {
    param([Parameter(Mandatory)][string]$RelativePath)
    $source = Join-Path $payload $RelativePath
    $destination = Join-Path $repo $RelativePath
    if (-not (Test-Path $source -PathType Leaf)) { throw "Payload file missing: $source" }
    New-Item -ItemType Directory -Path (Split-Path $destination -Parent) -Force | Out-Null
    Copy-Item $source $destination -Force
}

Set-Location $repo
$trackedStatus = @(& git status --porcelain --untracked-files=no)
if ($LASTEXITCODE -ne 0) { throw 'Unable to inspect repository status.' }
if ($trackedStatus.Count -gt 0) { throw 'Tracked working-tree changes are present.' }

& git fetch origin main
if ($LASTEXITCODE -ne 0) { throw 'Unable to fetch origin/main.' }
& git switch -C feature/sprint2-build088 origin/main
if ($LASTEXITCODE -ne 0) { throw 'Unable to create Build088 branch from origin/main.' }

$files = @(
# Build088 explicit lifecycle-contract installation.
$payloadContract = Join-Path $PSScriptRoot "payload\scripts\release\release-lifecycle-contract.json"
$repositoryContract = Join-Path $RepositoryRoot "scripts\release\release-lifecycle-contract.json"

if (-not (Test-Path $payloadContract -PathType Leaf)) {
    throw "Build088 payload contract is missing: $payloadContract"
}

New-Item `
    -ItemType Directory `
    -Path (Split-Path $repositoryContract -Parent) `
    -Force | Out-Null

Copy-Item `
    -Path $payloadContract `
    -Destination $repositoryContract `
    -Force
    'scripts/release/Invoke-NrhisSelfContainedBuild.ps1',
    'scripts/release/New-NrhisBuildPackage.ps1',
    'tests/test_release_self_contained_build_build088.py',
    'docs/Operations/BUILD088_SELF_CONTAINED_ONE_STEP.md',
    'docs/releases/BUILD088.md',
    'docs/releases/BUILD088_PR.md',
    'docs/releases/BUILD088_RELEASE_NOTES.md'
)
foreach ($file in $files) { Copy-PayloadFile $file }

python -m ruff check scripts/release tests/test_release_self_contained_build_build088.py
if ($LASTEXITCODE -ne 0) { throw 'Build088 Ruff validation failed.' }
python -m pytest tests/test_release_self_contained_build_build088.py -q
if ($LASTEXITCODE -ne 0) { throw 'Build088 deterministic tests failed.' }
# Build088 explicit lifecycle-contract installation.
$payloadContract = Join-Path $PSScriptRoot "payload\scripts\release\release-lifecycle-contract.json"
$repositoryContract = Join-Path $RepositoryRoot "scripts\release\release-lifecycle-contract.json"

if (-not (Test-Path $payloadContract -PathType Leaf)) {
    throw "Build088 payload contract is missing: $payloadContract"
}

New-Item `
    -ItemType Directory `
    -Path (Split-Path $repositoryContract -Parent) `
    -Force | Out-Null

Copy-Item `
    -Path $payloadContract `
    -Destination $repositoryContract `
    -Force

& (Join-Path $repo 'scripts/release/Invoke-NrhisSelfContainedBuild.ps1') `
    -BuildNumber '088' `
    -CommitMessage 'Build088: add self-contained one-step lifecycle' `
    -PullRequestTitle 'Build088: add self-contained one-step lifecycle' `
    -PullRequestBodyFile (Join-Path $repo 'docs/releases/BUILD088_PR.md') `
    -ReleaseTag 'v0.1.1-build088' `
    -ReleaseTitle 'NRHIS Sprint 2 Build088' `
    -ReleaseNotesFile (Join-Path $repo 'docs/releases/BUILD088_RELEASE_NOTES.md') `
    -RepositoryRoot $repo
