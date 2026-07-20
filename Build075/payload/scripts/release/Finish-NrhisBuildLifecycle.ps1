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

$state = (& gh pr view $PullRequestUrl --json state --jq '.state').Trim()
if ($LASTEXITCODE -ne 0) { throw "Unable to read pull-request state: $PullRequestUrl" }

if ($state -ne 'MERGED') {
    Write-Host 'Monitoring required CI checks...' -ForegroundColor Cyan
    & gh pr checks $PullRequestUrl --watch --fail-fast
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Resume with: .\scripts\release\Resume-NrhisBuildLifecycle.ps1 -BuildNumber '$BuildNumber'" -ForegroundColor Yellow
        throw "Build$BuildNumber CI failed. Automatic merge blocked."
    }

    Write-Host "Required CI checks passed for Build$BuildNumber." -ForegroundColor Green
    & gh pr merge $PullRequestUrl --merge
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Resume with: .\scripts\release\Resume-NrhisBuildLifecycle.ps1 -BuildNumber '$BuildNumber'" -ForegroundColor Yellow
        throw "Build$BuildNumber automatic merge failed."
    }
}
else {
    Write-Host "Build$BuildNumber pull request is already merged; continuing closeout." -ForegroundColor Cyan
}

$featureBranch = "feature/sprint2-build$BuildNumber"
git switch $BaseBranch
if ($LASTEXITCODE -ne 0) { throw "Unable to switch to $BaseBranch after merge." }

git fetch origin --tags
if ($LASTEXITCODE -ne 0) { throw 'Git fetch failed after merge.' }

git pull --ff-only origin $BaseBranch
if ($LASTEXITCODE -ne 0) { throw "Unable to fast-forward local $BaseBranch after merge." }

$localBranch = (& git branch --list $featureBranch).Trim()
if (-not [string]::IsNullOrWhiteSpace($localBranch)) {
    & git branch -D $featureBranch
    if ($LASTEXITCODE -ne 0) { throw "Unable to delete local feature branch: $featureBranch" }
}
else {
    Write-Host "Local feature branch already absent: $featureBranch" -ForegroundColor DarkGray
}

$remoteBranch = (& git ls-remote --heads origin "refs/heads/$featureBranch").Trim()
if ($LASTEXITCODE -ne 0) { throw "Unable to inspect remote feature branch: $featureBranch" }
if (-not [string]::IsNullOrWhiteSpace($remoteBranch)) {
    & git push origin --delete $featureBranch
    if ($LASTEXITCODE -ne 0) { throw "Unable to delete remote feature branch: $featureBranch" }
}
else {
    Write-Host "Remote feature branch already absent: $featureBranch" -ForegroundColor DarkGray
}

$evidenceRoot = Join-Path $HOME "NRHIS-Release-Evidence\Build$BuildNumber"
$completionReceipt = Join-Path $evidenceRoot 'completion-receipt.json'
if (-not (Test-Path $completionReceipt -PathType Leaf)) {
    $completionScript = Join-Path $repo "Build$BuildNumber\Complete-Build$BuildNumber.ps1"
    if (-not (Test-Path $completionScript -PathType Leaf)) {
        throw "Build completion script not found after merge: $completionScript"
    }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $completionScript -RepositoryRoot $repo
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Resume with: .\scripts\release\Resume-NrhisBuildLifecycle.ps1 -BuildNumber '$BuildNumber'" -ForegroundColor Yellow
        throw "Build$BuildNumber completion failed with exit code $LASTEXITCODE."
    }
}
else {
    Write-Host "Build$BuildNumber completion receipt already exists; skipping duplicate completion." -ForegroundColor Cyan
}

if (-not $SkipArchive) {
    $archiveDir = Join-Path $evidenceRoot 'installer-archive'
    $archiveManifest = Join-Path $archiveDir 'installer-archive-manifest.json'
    if (-not (Test-Path $archiveManifest -PathType Leaf)) {
        $archiveScript = Join-Path $repo 'scripts\release\Archive-NrhisInstallerArtifacts.ps1'
        if (-not (Test-Path $archiveScript -PathType Leaf)) {
            throw "Installer archive helper not found: $archiveScript"
        }

        & $archiveScript -BuildNumber $BuildNumber -RepositoryRoot $repo
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Resume with: .\scripts\release\Resume-NrhisBuildLifecycle.ps1 -BuildNumber '$BuildNumber'" -ForegroundColor Yellow
            throw "Build$BuildNumber installer archival failed with exit code $LASTEXITCODE."
        }
    }
    else {
        Write-Host "Build$BuildNumber installer archive already exists; skipping duplicate archival." -ForegroundColor Cyan
    }
}

Write-Host "Build$BuildNumber completed and verified." -ForegroundColor Green
$nextBuild = '{0:D3}' -f ([int]$BuildNumber + 1)
Write-Host 'lets move on to next build' -ForegroundColor Yellow
Write-Host "Waiting for Build$nextBuild root ZIP." -ForegroundColor Yellow
