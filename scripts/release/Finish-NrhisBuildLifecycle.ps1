[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^\d{3}$')][string]$BuildNumber,
    [Parameter(Mandatory)][string]$PullRequestUrl,
    [string]$RepositoryRoot = (Get-Location).Path,
    [string]$BaseBranch = 'develop',
    [switch]$SkipArchive
)

$ErrorActionPreference = 'Stop'

# Build081 automatic pull-request resolution
$placeholderValues = @(
    'PASTE_ACTUAL_PR_URL_HERE',
    'PASTE_THE_PR_URL_RETURNED_ABOVE',
    'PASTE_PR_URL_HERE'
)

$needsResolution = [string]::IsNullOrWhiteSpace($PullRequestUrl) -or ($placeholderValues -contains $PullRequestUrl.Trim())
if ($needsResolution) {
    $resolver = Join-Path $RepositoryRoot 'scripts/release/Resolve-NrhisPullRequest.ps1'
    if (-not (Test-Path $resolver -PathType Leaf)) {
        throw "Pull-request resolver not found: $resolver"
    }

    $PullRequestUrl = & $resolver -BuildNumber $BuildNumber -RepositoryRoot $RepositoryRoot
}

if ($PullRequestUrl -notmatch '^https://github\.com/[^/]+/[^/]+/pull/\d+$') {
    throw "Invalid pull-request URL: $PullRequestUrl"
}
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo

function Write-LifecycleState {
    param(
        [Parameter(Mandatory)][string]$Phase,
        [Parameter(Mandatory)][string]$Status,
        [string]$Detail
    )

    $stateDir = Join-Path $HOME "NRHIS-Release-Evidence\Build$BuildNumber"
    New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
    $statePath = Join-Path $stateDir 'lifecycle-state.json'
    $record = [ordered]@{
        schema_version = 1
        build = $BuildNumber
        phase = $Phase
        status = $Status
        detail = $Detail
        pull_request_url = $PullRequestUrl
        base_branch = $BaseBranch
        updated_at = [DateTime]::UtcNow.ToString('o')
    }
    $json = $record | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText($statePath, $json + "`n", [System.Text.UTF8Encoding]::new($false))
}

Write-LifecycleState -Phase 'initialization' -Status 'running' -Detail 'Release lifecycle started.'

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'GitHub CLI (gh) is required for CI monitoring and automatic merge.'
}

& gh auth status 1>$null 2>$null
if ($LASTEXITCODE -ne 0) {
    throw 'GitHub CLI is not authenticated. Run: gh auth login'
}

$state = (@(& gh pr view $PullRequestUrl --json state --jq '.state') -join "`n").Trim()
if ($LASTEXITCODE -ne 0) { throw "Unable to read pull-request state: $PullRequestUrl" }

if ($state -ne 'MERGED') {
    Write-LifecycleState -Phase 'ci' -Status 'running' -Detail 'Monitoring required CI checks.'
    Write-Host 'Monitoring required CI checks...' -ForegroundColor Cyan
    & gh pr checks $PullRequestUrl --watch --fail-fast
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Resume with: .\scripts\release\Resume-NrhisBuildLifecycle.ps1 -BuildNumber '$BuildNumber'" -ForegroundColor Yellow
        throw "Build$BuildNumber CI failed. Automatic merge blocked."
    }

    Write-LifecycleState -Phase 'ci' -Status 'passed' -Detail 'Required CI checks passed.'
    Write-Host "Required CI checks passed for Build$BuildNumber." -ForegroundColor Green
    Write-LifecycleState -Phase 'merge' -Status 'running' -Detail 'Merging pull request.'
    & gh pr merge $PullRequestUrl --merge
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Resume with: .\scripts\release\Resume-NrhisBuildLifecycle.ps1 -BuildNumber '$BuildNumber'" -ForegroundColor Yellow
        throw "Build$BuildNumber automatic merge failed."
    }
}
else {
    Write-LifecycleState -Phase 'merge' -Status 'passed' -Detail 'Pull request already merged.'
    Write-Host "Build$BuildNumber pull request is already merged; continuing closeout." -ForegroundColor Cyan
}

$featureBranch = "feature/sprint2-build$BuildNumber"
Write-LifecycleState -Phase 'synchronize' -Status 'running' -Detail "Synchronizing $BaseBranch."
git switch $BaseBranch
if ($LASTEXITCODE -ne 0) { throw "Unable to switch to $BaseBranch after merge." }

git fetch origin --tags
if ($LASTEXITCODE -ne 0) { throw 'Git fetch failed after merge.' }

git pull --ff-only origin $BaseBranch
if ($LASTEXITCODE -ne 0) { throw "Unable to fast-forward local $BaseBranch after merge." }

$localBranch = (@(& git branch --list $featureBranch) -join "`n").Trim()
if (-not [string]::IsNullOrWhiteSpace($localBranch)) {
    & git branch -D $featureBranch
    if ($LASTEXITCODE -ne 0) { throw "Unable to delete local feature branch: $featureBranch" }
}
else {
    Write-Host "Local feature branch already absent: $featureBranch" -ForegroundColor DarkGray
}

$remoteBranch = (@(& git ls-remote --heads origin "refs/heads/$featureBranch") -join "`n").Trim()
if ($LASTEXITCODE -ne 0) { throw "Unable to inspect remote feature branch: $featureBranch" }
if (-not [string]::IsNullOrWhiteSpace($remoteBranch)) {
    & git push origin --delete $featureBranch
    if ($LASTEXITCODE -ne 0) { throw "Unable to delete remote feature branch: $featureBranch" }
}
else {
    Write-Host "Remote feature branch already absent: $featureBranch" -ForegroundColor DarkGray
}

Write-LifecycleState -Phase 'cleanup' -Status 'passed' -Detail 'Feature branch cleanup complete.'

$evidenceRoot = Join-Path $HOME "NRHIS-Release-Evidence\Build$BuildNumber"
$completionReceipt = Join-Path $evidenceRoot 'completion-receipt.json'
if (-not (Test-Path $completionReceipt -PathType Leaf)) {
    $completionScript = Join-Path $repo "Build$BuildNumber\Complete-Build$BuildNumber.ps1"
    if (-not (Test-Path $completionScript -PathType Leaf)) {
        throw "Build completion script not found after merge: $completionScript"
    }

    Write-LifecycleState -Phase 'completion' -Status 'running' -Detail 'Running build completion script.'
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
    if (-not (Test-Path $completionReceipt -PathType Leaf)) {
        throw "Completion receipt missing after completion: $completionReceipt"
    }
    $receipt = Get-Content $completionReceipt -Raw | ConvertFrom-Json
    if ([string]$receipt.status -ne 'verified' -or $receipt.verified -ne $true) {
        throw 'Completion receipt is not archive-compatible. Expected status=verified and verified=true.'
    }

    $archiveDir = Join-Path $evidenceRoot 'installer-archive'
    $archiveManifest = Join-Path $archiveDir 'installer-archive-manifest.json'
    if (-not (Test-Path $archiveManifest -PathType Leaf)) {
        $archiveScript = Join-Path $repo 'scripts\release\Archive-NrhisInstallerArtifacts.ps1'
        if (-not (Test-Path $archiveScript -PathType Leaf)) {
            throw "Installer archive helper not found: $archiveScript"
        }

        Write-LifecycleState -Phase 'archive' -Status 'running' -Detail 'Archiving installer artifacts.'
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

Write-LifecycleState -Phase 'closed' -Status 'completed' -Detail 'Build completed, verified, and archived.'
Write-Host "Build$BuildNumber completed and verified." -ForegroundColor Green
$nextBuild = '{0:D3}' -f ([int]$BuildNumber + 1)
Write-Host 'lets move on to next build' -ForegroundColor Yellow
Write-Host "Waiting for Build$nextBuild root ZIP." -ForegroundColor Yellow
