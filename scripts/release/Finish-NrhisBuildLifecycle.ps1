[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^\d{3}$')][string]$BuildNumber,
    [Parameter(Mandatory)][string]$PullRequestUrl,
    [string]$RepositoryRoot = (Get-Location).Path,
    [string]$BaseBranch = 'develop',
    [switch]$SkipArchive
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'GitHub CLI (gh) is required for CI monitoring and automatic merge.'
}

& gh auth status 1>$null 2>$null
if ($LASTEXITCODE -ne 0) {
    throw 'GitHub CLI is not authenticated. Run: gh auth login'
}

Write-Host 'Monitoring required CI checks...' -ForegroundColor Cyan
& gh pr checks $PullRequestUrl --watch --fail-fast
if ($LASTEXITCODE -ne 0) {
    throw "Build$BuildNumber CI failed. Automatic merge blocked."
}

Write-Host "Required CI checks passed for Build$BuildNumber." -ForegroundColor Green
& gh pr merge $PullRequestUrl --merge
if ($LASTEXITCODE -ne 0) {
    throw "Build$BuildNumber automatic merge failed."
}

$featureBranch = "feature/sprint2-build$BuildNumber"

git switch $BaseBranch
if ($LASTEXITCODE -ne 0) { throw "Unable to switch to $BaseBranch after merge." }

git fetch origin --tags
if ($LASTEXITCODE -ne 0) { throw 'Git fetch failed after merge.' }

git pull --ff-only origin $BaseBranch
if ($LASTEXITCODE -ne 0) { throw "Unable to fast-forward local $BaseBranch after merge." }

# Delete the feature branch only after the local base branch is current.
git branch -D $featureBranch 2>$null
& git push origin --delete $featureBranch 2>$null

$completionScript = Join-Path $repo "Build$BuildNumber\Complete-Build$BuildNumber.ps1"
if (-not (Test-Path $completionScript -PathType Leaf)) {
    throw "Build completion script not found after merge: $completionScript"
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $completionScript -RepositoryRoot $repo
if ($LASTEXITCODE -ne 0) {
    throw "Build$BuildNumber completion failed with exit code $LASTEXITCODE."
}

if (-not $SkipArchive) {
    $archiveScript = Join-Path $repo 'scripts\release\Archive-NrhisInstallerArtifacts.ps1'
    if (-not (Test-Path $archiveScript -PathType Leaf)) {
        throw "Installer archive helper not found: $archiveScript"
    }

    & $archiveScript -BuildNumber $BuildNumber -RepositoryRoot $repo
    if ($LASTEXITCODE -ne 0) {
        throw "Build$BuildNumber installer archival failed with exit code $LASTEXITCODE."
    }
}

Write-Host "Build$BuildNumber completed and verified." -ForegroundColor Green
$nextBuild = '{0:D3}' -f ([int]$BuildNumber + 1)
Write-Host 'lets move on to next build' -ForegroundColor Yellow
Write-Host "Waiting for Build$nextBuild root ZIP." -ForegroundColor Yellow
