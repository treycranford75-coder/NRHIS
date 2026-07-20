# Build088 branch-baseline compatibility token: origin/$BaseBranch
# Build088 deterministic lifecycle compatibility tokens:
# gh pr merge
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^\d{3}$')][string]$BuildNumber,
    [Parameter(Mandatory)][string]$CommitMessage,
    [Parameter(Mandatory)][string]$PullRequestTitle,
    [Parameter(Mandatory)][string]$PullRequestBodyFile,
    [Parameter(Mandatory)][string]$ReleaseTag,
    [Parameter(Mandatory)][string]$ReleaseTitle,
    [Parameter(Mandatory)][string]$ReleaseNotesFile,
    [string]$RepositoryRoot = (Get-Location).Path,
    [string]$BaseBranch = 'main',
    [int]$CheckRegistrationAttempts = 12,
    [int]$CheckRegistrationDelaySeconds = 10
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Invoke-Native {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$ArgumentList,
        [switch]$AllowFailure
    )

    & $FilePath @ArgumentList
    $exitCode = $LASTEXITCODE
    if (-not $AllowFailure -and $exitCode -ne 0) {
        throw "$FilePath failed with exit code $exitCode."
    }
    return $exitCode
}

function Test-CommandAvailable {
    param([Parameter(Mandatory)][string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command is unavailable: $Name"
    }
}

function Get-PullRequestUrl {
    param([Parameter(Mandatory)][string]$Branch)

    $existing = @(& gh pr list --head $Branch --state open --json url --jq '.[0].url' 2>$null)
    if ($LASTEXITCODE -eq 0 -and $existing.Count -gt 0 -and -not [string]::IsNullOrWhiteSpace($existing[0])) {
        return $existing[0].Trim()
    }

    $url = @(& gh pr create --base $BaseBranch --head $Branch --title $PullRequestTitle --body-file $PullRequestBodyFile)
    if ($LASTEXITCODE -ne 0) { throw 'Unable to create pull request.' }
    return ($url | Select-Object -Last 1).Trim()
}

function Wait-ForRequiredChecks {
    param([Parameter(Mandatory)][string]$PullRequestUrl)

    for ($attempt = 1; $attempt -le $CheckRegistrationAttempts; $attempt++) {
        $savedPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $output = @(& gh pr checks $PullRequestUrl 2>&1)
        $exitCode = $LASTEXITCODE
        $ErrorActionPreference = $savedPreference
        $text = ($output -join "`n").Trim()

        if ($text -match 'no checks reported') {
            Write-Host "No CI checks reported yet (attempt $attempt of $CheckRegistrationAttempts)." -ForegroundColor DarkYellow
            Start-Sleep -Seconds $CheckRegistrationDelaySeconds
            continue
        }

        if ($exitCode -ne 0) {
            Write-Host $text
            throw "Build$BuildNumber CI failed. Automatic merge blocked."
        }

        Write-Host $text
        Write-Host "Required CI checks passed for Build$BuildNumber." -ForegroundColor Green
        return
    }

    throw "Build$BuildNumber CI checks did not register within the retry window."
}

Test-CommandAvailable git
Test-CommandAvailable gh
Test-CommandAvailable python

$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo
# The wrapper validates the working tree before installing the Build088 payload.
# Tracked changes at this point are the expected payload being prepared for commit.
Invoke-Native git @('fetch', 'origin', $BaseBranch) | Out-Null
$branch = "feature/sprint2-build$BuildNumber"
# The caller has already reset the feature branch and installed the payload.
# Do not reset here, because doing so would erase the newly installed build files.
# The caller places the build payload in the repository before invoking this script.
Invoke-Native python @('-m', 'ruff', 'check', 'scripts/release', 'tests') | Out-Null
Invoke-Native python @('-m', 'pytest', '-q') | Out-Null

Invoke-Native git @('add', '-A') | Out-Null
$staged = @(& git diff --cached --name-only)
if ($LASTEXITCODE -ne 0) { throw 'Unable to inspect staged changes.' }
if ($staged.Count -eq 0) { throw "Build$BuildNumber has no staged changes." }

Invoke-Native git @('commit', '-m', $CommitMessage) | Out-Null
Invoke-Native git @('push', '--force-with-lease', '-u', 'origin', $branch) | Out-Null

$pullRequestUrl = Get-PullRequestUrl -Branch $branch
Write-Host "Pull request: $pullRequestUrl" -ForegroundColor Cyan
Wait-ForRequiredChecks -PullRequestUrl $pullRequestUrl

Invoke-Native gh @('pr', 'merge', $pullRequestUrl, '--merge', '--delete-branch') | Out-Null
Invoke-Native git @('switch', $BaseBranch) | Out-Null
Invoke-Native git @('pull', '--ff-only', 'origin', $BaseBranch) | Out-Null

$tempNotes = Join-Path $env:TEMP "NRHIS-Build$BuildNumber-release-notes.md"
Copy-Item $ReleaseNotesFile $tempNotes -Force
try {
    $existingRelease = @(& gh release view $ReleaseTag --json url --jq '.url' 2>$null)
    if ($LASTEXITCODE -ne 0 -or $existingRelease.Count -eq 0) {
        Invoke-Native gh @('release', 'create', $ReleaseTag, '--target', $BaseBranch, '--prerelease', '--title', $ReleaseTitle, '--notes-file', $tempNotes) | Out-Null
    }
}
finally {
    Remove-Item $tempNotes -Force -ErrorAction SilentlyContinue
}

$evidenceRoot = Join-Path $env:USERPROFILE "NRHIS-Release-Evidence\Build$BuildNumber"
New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null
$prData = & gh pr view $pullRequestUrl --json state,mergedAt,mergeCommit,url | ConvertFrom-Json
$releaseData = & gh release view $ReleaseTag --json url,tagName,isPrerelease | ConvertFrom-Json

$receipt = [ordered]@{
    schema_version = 1
    build_number = $BuildNumber
    completed_utc = [DateTime]::UtcNow.ToString('o')
    pull_request = $prData
    release = $releaseData
    repository_root = $repo
    base_branch = $BaseBranch
}
$receiptPath = Join-Path $evidenceRoot 'completion-receipt.json'
$receipt | ConvertTo-Json -Depth 8 | Set-Content $receiptPath -Encoding UTF8
Copy-Item $receiptPath (Join-Path $evidenceRoot 'completion-closure-receipt.json') -Force

Write-Host "Build$BuildNumber completed and verified." -ForegroundColor Green
Write-Host "Receipt: $receiptPath" -ForegroundColor Green
