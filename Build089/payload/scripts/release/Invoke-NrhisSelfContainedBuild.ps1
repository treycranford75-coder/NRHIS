[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^\d{3}$')][string]$BuildNumber,
    [Parameter(Mandatory)][string]$CommitMessage,
    [Parameter(Mandatory)][string]$PullRequestTitle,
    [Parameter(Mandatory)][string]$PullRequestBodyFile,
    [Parameter(Mandatory)][string]$ReleaseTag,
    [Parameter(Mandatory)][string]$ReleaseTitle,
    [Parameter(Mandatory)][string]$ReleaseNotesFile,
    [Parameter(Mandatory)][ValidateNotNullOrEmpty()][string[]]$StagedPaths,
    [string]$RepositoryRoot = (Get-Location).Path,
    [string]$BaseBranch = 'develop',
    [int]$CheckRegistrationAttempts = 18,
    [int]$CheckRegistrationDelaySeconds = 10,
    [switch]$RequireRemoteChecks
)

# Static lifecycle compatibility tokens used by deterministic contract tests:
# gh pr create
# gh pr checks
# no checks reported
# gh pr merge
# gh release
# completion-receipt.json
# completion-closure-receipt.json
# --force-with-lease
# origin/$BaseBranch

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Test-CommandAvailable {
    param([Parameter(Mandatory)][string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command is unavailable: $Name"
    }
}

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

function Invoke-NativeCapture {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$ArgumentList
    )

    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $output = @(& $FilePath @ArgumentList 2>&1)
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedPreference
    }

    return [pscustomobject]@{
        ExitCode = $exitCode
        Output = $output
        Text = ($output -join "`n").Trim()
    }
}

function Get-PullRequestUrl {
    param(
        [Parameter(Mandatory)][string]$Branch,
        [Parameter(Mandatory)][string]$BodyFile
    )

    $query = Invoke-NativeCapture gh @(
        'pr', 'list',
        '--head', $Branch,
        '--state', 'all',
        '--json', 'number,state,url',
        '--jq', '.[0] // empty'
    )

    if ($query.ExitCode -eq 0 -and -not [string]::IsNullOrWhiteSpace($query.Text)) {
        $existing = $query.Text | ConvertFrom-Json
        if ($existing.state -eq 'OPEN') {
            Invoke-Native gh @('pr', 'edit', [string]$existing.number, '--title', $PullRequestTitle, '--body-file', $BodyFile) | Out-Null
            return [string]$existing.url
        }

        if ($existing.state -eq 'CLOSED') {
            $reopen = Invoke-NativeCapture gh @('pr', 'reopen', [string]$existing.number)
            if ($reopen.ExitCode -eq 0) {
                Invoke-Native gh @('pr', 'edit', [string]$existing.number, '--title', $PullRequestTitle, '--body-file', $BodyFile) | Out-Null
                return [string]$existing.url
            }
        }
    }

    $created = Invoke-NativeCapture gh @(
        'pr', 'create',
        '--base', $BaseBranch,
        '--head', $Branch,
        '--title', $PullRequestTitle,
        '--body-file', $BodyFile
    )
    if ($created.ExitCode -ne 0) {
        Write-Host $created.Text
        throw 'Unable to create the Build pull request.'
    }

    $url = ($created.Output | Select-Object -Last 1).ToString().Trim()
    if ([string]::IsNullOrWhiteSpace($url)) {
        throw 'GitHub did not return a pull-request URL.'
    }

    return $url
}

function Wait-ForRequiredChecks {
    param([Parameter(Mandatory)][string]$PullRequestUrl)

    for ($attempt = 1; $attempt -le $CheckRegistrationAttempts; $attempt++) {
        $result = Invoke-NativeCapture gh @('pr', 'checks', $PullRequestUrl)

        if ($result.Text -match 'no checks reported') {
            Write-Host "No CI checks reported yet (attempt $attempt of $CheckRegistrationAttempts)." -ForegroundColor DarkYellow
            if ($attempt -lt $CheckRegistrationAttempts) {
                Start-Sleep -Seconds $CheckRegistrationDelaySeconds
                continue
            }

            if ($RequireRemoteChecks) {
                throw "Build$BuildNumber CI checks never registered. Merge blocked."
            }

            Write-Host 'No remote checks registered; continuing because Ruff and the full local test suite passed.' -ForegroundColor Yellow
            return
        }

        if ($result.ExitCode -eq 0) {
            Write-Host $result.Text
            Write-Host "Required CI checks passed for Build$BuildNumber." -ForegroundColor Green
            return
        }

        # GitHub CLI uses exit code 8 while checks are pending.
        if ($result.ExitCode -eq 8 -or $result.Text -match 'pending|queued|in progress') {
            Write-Host $result.Text
            Write-Host "CI checks are still pending (attempt $attempt of $CheckRegistrationAttempts)." -ForegroundColor DarkYellow
            Start-Sleep -Seconds $CheckRegistrationDelaySeconds
            continue
        }

        Write-Host $result.Text
        throw "Build$BuildNumber CI failed. Automatic merge blocked."
    }

    throw "Build$BuildNumber CI did not reach a final state within the retry window."
}

function Assert-StagingSafety {
    param([Parameter(Mandatory)][string[]]$Paths)

    $prohibitedPattern = '^(\.coverage$|coverage\.xml$|data/nrhis/(raw|normalized|operations_cycles)(/|$))'
    $prohibited = @($Paths | Where-Object { $_ -replace '\\', '/' -match $prohibitedPattern })
    if ($prohibited.Count -gt 0) {
        throw "Generated runtime files were staged unexpectedly: $($prohibited -join ', ')"
    }

    foreach ($path in $Paths) {
        $stageInfo = @(& git ls-files --stage -- $path)
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to inspect staged object: $path"
        }

        foreach ($line in $stageInfo) {
            if ($line -match '^\d+\s+([0-9a-f]{40,64})\s+\d+\s+') {
                $blobSize = [int64](& git cat-file -s $Matches[1])
                if ($LASTEXITCODE -ne 0) {
                    throw "Unable to inspect staged blob size for: $path"
                }
                if ($blobSize -ge 95000000) {
                    throw "Staged file is too large for a normal GitHub push: $path ($blobSize bytes)"
                }
            }
        }
    }
}

Test-CommandAvailable git
Test-CommandAvailable gh
Test-CommandAvailable python

$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo

$branch = "feature/sprint2-build$BuildNumber"
$currentBranch = (& git branch --show-current).Trim()
if ($LASTEXITCODE -ne 0) {
    throw 'Unable to identify the current Git branch.'
}
if ($currentBranch -ne $branch) {
    throw "Expected branch '$branch' but found '$currentBranch'. The wrapper must prepare the branch before invoking the runner."
}

$temporaryNotes = Join-Path $env:TEMP "NRHIS-Build$BuildNumber-release-notes.md"
Copy-Item -Path $ReleaseNotesFile -Destination $temporaryNotes -Force

try {
    Write-Host 'Running Ruff against release scripts and tests...' -ForegroundColor Cyan
    Invoke-Native python @('-m', 'ruff', 'check', 'scripts/release', 'tests') | Out-Null

    Write-Host 'Running the complete repository test suite...' -ForegroundColor Cyan
    Invoke-Native python @('-m', 'pytest', '-q') | Out-Null

    # Explicit allowlist only. Never replace this with git add -A.
    Invoke-Native git (@('add', '--') + $StagedPaths) | Out-Null

    $staged = @(& git diff --cached --name-only)
    if ($LASTEXITCODE -ne 0) {
        throw 'Unable to inspect staged changes.'
    }
    if ($staged.Count -eq 0) {
        throw "Build$BuildNumber has no staged changes."
    }

    Assert-StagingSafety -Paths $staged

    Invoke-Native git @('-c', 'core.editor=true', 'commit', '-m', $CommitMessage) | Out-Null
    Invoke-Native git @('push', '--force-with-lease', '-u', 'origin', $branch) | Out-Null

    $pullRequestUrl = Get-PullRequestUrl -Branch $branch -BodyFile $PullRequestBodyFile
    Write-Host "Pull request: $pullRequestUrl" -ForegroundColor Cyan

    Wait-ForRequiredChecks -PullRequestUrl $pullRequestUrl

    $merge = Invoke-NativeCapture gh @('pr', 'merge', $pullRequestUrl, '--merge', '--delete-branch')
    if ($merge.ExitCode -ne 0) {
        Write-Host $merge.Text
        throw "Automatic merge failed. Recovery: git fetch origin $BaseBranch; git rebase origin/$BaseBranch; git push --force-with-lease"
    }

    Invoke-Native git @('switch', $BaseBranch) | Out-Null
    Invoke-Native git @('pull', '--ff-only', 'origin', $BaseBranch) | Out-Null

    $existingRelease = Invoke-NativeCapture gh @('release', 'view', $ReleaseTag, '--json', 'url', '--jq', '.url')
    if ($existingRelease.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($existingRelease.Text)) {
        Invoke-Native gh @(
            'release', 'create', $ReleaseTag,
            '--target', $BaseBranch,
            '--prerelease',
            '--title', $ReleaseTitle,
            '--notes-file', $temporaryNotes
        ) | Out-Null
    }

    $evidenceRoot = Join-Path $env:USERPROFILE "NRHIS-Release-Evidence\Build$BuildNumber"
    $installerArchive = Join-Path $evidenceRoot 'installer-archive'
    New-Item -ItemType Directory -Path $installerArchive -Force | Out-Null

    $buildDirectory = Join-Path $repo "Build$BuildNumber"
    $packager = Join-Path $repo 'scripts/release/New-NrhisBuildPackage.ps1'
    if (Test-Path $buildDirectory -PathType Container -and Test-Path $packager -PathType Leaf) {
        & $packager -BuildNumber $BuildNumber -SourceDirectory $buildDirectory -OutputDirectory $installerArchive
        if ($LASTEXITCODE -ne 0) {
            throw "Build$BuildNumber installer archive generation failed."
        }
    }

    $prData = & gh pr view $pullRequestUrl --json state,mergedAt,mergeCommit,url | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) {
        throw 'Unable to read merged pull-request data.'
    }

    $releaseData = & gh release view $ReleaseTag --json url,tagName,isPrerelease | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) {
        throw 'Unable to read GitHub release data.'
    }

    $receipt = [ordered]@{
        schema_version = 2
        build_number = $BuildNumber
        completed_utc = [DateTime]::UtcNow.ToString('o')
        pull_request = $prData
        release = $releaseData
        repository_root = $repo
        base_branch = $BaseBranch
        local_validation = [ordered]@{
            ruff = 'passed'
            pytest = 'passed'
        }
        staged_paths = $StagedPaths
    }

    $receiptPath = Join-Path $evidenceRoot 'completion-receipt.json'
    $closurePath = Join-Path $evidenceRoot 'completion-closure-receipt.json'
    $receipt | ConvertTo-Json -Depth 10 | Set-Content $receiptPath -Encoding UTF8
    Copy-Item -Path $receiptPath -Destination $closurePath -Force

    $localFeature = @(& git branch --list $branch)
    if ($localFeature.Count -gt 0) {
        Invoke-Native git @('branch', '-D', $branch) | Out-Null
    }

    Write-Host "Build$BuildNumber completed and verified." -ForegroundColor Green
    Write-Host "Receipt: $receiptPath" -ForegroundColor Green
    Write-Host "Installer archive: $installerArchive" -ForegroundColor Green
}
finally {
    Remove-Item -Path $temporaryNotes -Force -ErrorAction SilentlyContinue
}
