[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$BuildNumber,
    [Parameter(Mandatory)][string]$Repository,
    [Parameter(Mandatory)][string]$Branch,
    [Parameter(Mandatory)][string]$CommitMessage,
    [Parameter(Mandatory)][string]$PullRequestTitle,
    [Parameter(Mandatory)][string]$PullRequestBodyFile,
    [Parameter(Mandatory)][string]$Tag,
    [Parameter(Mandatory)][string]$ReleaseTitle,
    [Parameter(Mandatory)][string]$ReleaseNotesFile,
    [Parameter(Mandatory)][string]$PayloadRoot,
    [string]$EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence"),
    [string]$ReleaseAsset,
    [int]$WaitForMergeMinutes = 20,
    [switch]$BrowserOnly
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-Git([string[]]$Arguments, [string]$FailureMessage) {
    & git @Arguments
    if ($LASTEXITCODE -ne 0) { throw $FailureMessage }
}

function Test-GhAuthentication {
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { return $false }
    & gh auth status --hostname github.com 1>$null 2>$null
    return ($LASTEXITCODE -eq 0)
}

function Install-GitHubCliIfPossible {
    if (Get-Command gh -ErrorAction SilentlyContinue) { return }
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Installing GitHub CLI for full lifecycle automation..." -ForegroundColor Cyan
        winget install --id GitHub.cli --exact --silent --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) { Write-Warning "GitHub CLI installation did not complete." }
        $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
        $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
        $env:Path = "$machinePath;$userPath"
    }
}

function Ensure-GitHubAuthentication {
    if ($BrowserOnly) { return $false }
    Install-GitHubCliIfPossible
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { return $false }
    if (Test-GhAuthentication) { return $true }
    Write-Host "One-time GitHub authorization is required for full automation." -ForegroundColor Yellow
    gh auth login --hostname github.com --git-protocol https --web
    if ($LASTEXITCODE -ne 0) { return $false }
    return (Test-GhAuthentication)
}

function Copy-PayloadAuthoritatively {
    param([Parameter(Mandatory)][string]$Source, [Parameter(Mandatory)][string]$Destination)
    if (-not (Test-Path $Source)) { throw "Build payload is missing: $Source" }
    Get-ChildItem $Source -Recurse -File | ForEach-Object {
        $relative = $_.FullName.Substring($Source.Length).TrimStart([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
        $target = Join-Path $Destination $relative
        New-Item -ItemType Directory -Path (Split-Path $target) -Force | Out-Null
        Copy-Item $_.FullName $target -Force
        $sourceHash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
        $targetHash = (Get-FileHash $target -Algorithm SHA256).Hash
        if ($sourceHash -ne $targetHash) { throw "Payload consistency failure: $relative" }
    }
}

function Invoke-SyntaxAndTestGates {
    param([Parameter(Mandatory)][string]$RepoRoot)
    $parserErrors = @()
    Get-ChildItem (Join-Path $RepoRoot "scripts") -Recurse -Filter "*.ps1" -File | ForEach-Object {
        $tokens = $null
        $errors = $null
        [System.Management.Automation.Language.Parser]::ParseFile($_.FullName, [ref]$tokens, [ref]$errors) | Out-Null
        if ($errors.Count -gt 0) { $parserErrors += $errors }
    }
    if ($parserErrors.Count -gt 0) { throw ($parserErrors | Out-String) }
    Write-Host "PowerShell syntax validation passed." -ForegroundColor Green

    if (Get-Command ruff -ErrorAction SilentlyContinue) {
        ruff check .
        if ($LASTEXITCODE -ne 0) { throw "Ruff failed." }
    }
    if (Get-Command pytest -ErrorAction SilentlyContinue) {
        pytest --cov=src --cov-branch --cov-fail-under=80
        if ($LASTEXITCODE -ne 0) { throw "Pytest or branch-coverage gate failed." }
    }
    Invoke-Git -Arguments @("diff", "--check") -FailureMessage "Whitespace validation failed."
}

function Get-PullRequestRecord {
    param([Parameter(Mandatory)][string]$Repo, [Parameter(Mandatory)][string]$Head)
    $json = gh pr list --repo $Repo --head $Head --base develop --state all --limit 1 --json number,state,url,mergedAt,mergeStateStatus
    if ($LASTEXITCODE -ne 0 -or -not $json) { return $null }
    $items = $json | ConvertFrom-Json
    if ($items.Count -eq 0) { return $null }
    return $items[0]
}

function Open-PullRequestFallback {
    param([Parameter(Mandatory)][string]$Repo, [Parameter(Mandatory)][string]$Head)
    $url = "https://github.com/$Repo/compare/develop...$Head`?expand=1"
    Set-Clipboard -Value $url -ErrorAction SilentlyContinue
    try { Start-Process $url } catch { }
    Write-Host "Browser pull-request action required." -ForegroundColor Yellow
    Write-Host "Base: develop"
    Write-Host "Compare: $Head"
    Write-Host "Rerun the same command after the PR is merged."
}

$repoRoot = (Get-Location).Path
if (-not (Test-Path (Join-Path $repoRoot ".git"))) { throw "Run from the NRHIS repository root." }
Set-Location $repoRoot

$ghReady = Ensure-GitHubAuthentication
$current = (git branch --show-current).Trim()

# If the build is already merged, skip directly to release completion.
$buildDoc = Join-Path $repoRoot ("docs\releases\BUILD{0}.md" -f $BuildNumber)
if ($current -eq "develop") {
    Invoke-Git -Arguments @("fetch", "origin", "--no-prune", "--tags") -FailureMessage "Git fetch failed."
    Invoke-Git -Arguments @("pull", "--ff-only", "--no-prune", "origin", "develop") -FailureMessage "Git pull failed."
    if (-not (Test-Path $buildDoc)) {
        $remoteBranchExists = $false
        git show-ref --verify --quiet "refs/remotes/origin/$Branch"
        if ($LASTEXITCODE -eq 0) { $remoteBranchExists = $true }
        if ($remoteBranchExists) {
            Invoke-Git -Arguments @("switch", "--track", "origin/$Branch") -FailureMessage "Unable to switch to existing $Branch."
        } else {
            Invoke-Git -Arguments @("switch", "-c", $Branch) -FailureMessage "Unable to create $Branch."
        }
        $current = (git branch --show-current).Trim()
    }
}

if ($current -eq $Branch) {
    Copy-PayloadAuthoritatively -Source $PayloadRoot -Destination $repoRoot
    Invoke-SyntaxAndTestGates -RepoRoot $repoRoot
    git add --all
    if (-not (git diff --cached --quiet)) {
        Invoke-Git -Arguments @("commit", "-m", $CommitMessage) -FailureMessage "Commit failed."
        Invoke-Git -Arguments @("push", "-u", "origin", $Branch) -FailureMessage "Push failed."
    } else {
        Write-Host "No staged changes; payload-authoritative rerun is already applied."
        Invoke-Git -Arguments @("push", "-u", "origin", $Branch) -FailureMessage "Branch push failed."
    }

    if ($ghReady) {
        $pr = Get-PullRequestRecord -Repo $Repository -Head $Branch
        if ($null -eq $pr) {
            $url = gh pr create --repo $Repository --base develop --head $Branch --title $PullRequestTitle --body-file $PullRequestBodyFile
            if ($LASTEXITCODE -ne 0) { throw "Automatic pull-request creation failed." }
            Write-Host "Pull request created: $url" -ForegroundColor Green
            $pr = Get-PullRequestRecord -Repo $Repository -Head $Branch
        }
        if ($null -ne $pr -and $pr.state -eq "OPEN") {
            gh pr merge $pr.number --repo $Repository --auto --merge
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "Auto-merge could not be enabled. Opening the pull request for review."
                try { Start-Process $pr.url } catch { }
                return
            }
            Write-Host "Auto-merge enabled. Waiting for required checks..." -ForegroundColor Cyan
            $deadline = (Get-Date).AddMinutes($WaitForMergeMinutes)
            do {
                Start-Sleep -Seconds 15
                $pr = Get-PullRequestRecord -Repo $Repository -Head $Branch
                if ($null -ne $pr -and $pr.state -eq "MERGED") { break }
            } while ((Get-Date) -lt $deadline)
            if ($null -eq $pr -or $pr.state -ne "MERGED") {
                Write-Host "Pull request remains open. Rerun the same command after merge." -ForegroundColor Yellow
                if ($null -ne $pr) { Write-Host "PR: $($pr.url)" }
                return
            }
        }
    } else {
        Open-PullRequestFallback -Repo $Repository -Head $Branch
        return
    }
}

# Confirm the feature is merged before releasing.
if ($ghReady) {
    $pr = Get-PullRequestRecord -Repo $Repository -Head $Branch
    if ($null -ne $pr -and $pr.state -ne "MERGED") {
        Write-Host "Build$BuildNumber PR is not merged. Rerun after merge." -ForegroundColor Yellow
        Write-Host "PR: $($pr.url)"
        return
    }
}

Invoke-Git -Arguments @("switch", "develop") -FailureMessage "Unable to switch to develop."
Invoke-Git -Arguments @("fetch", "origin", "--no-prune", "--tags") -FailureMessage "Git fetch failed."
Invoke-Git -Arguments @("pull", "--ff-only", "--no-prune", "origin", "develop") -FailureMessage "Git pull failed."
if (-not (Test-Path $buildDoc)) { throw "Build$BuildNumber is not present on develop; merge verification failed." }

$completion = Join-Path $repoRoot "scripts\release\Complete-NrhisAutomatedRelease.ps1"
if (-not (Test-Path $completion)) { throw "Missing automated release helper: $completion" }
$params = @{
    BuildNumber = $BuildNumber
    Repository = $Repository
    Tag = $Tag
    ReleaseTitle = $ReleaseTitle
    NotesFile = $ReleaseNotesFile
    EvidenceRoot = $EvidenceRoot
}
if ($ReleaseAsset -and (Test-Path $ReleaseAsset)) { $params.ReleaseAsset = $ReleaseAsset }
if ($BrowserOnly) { $params.BrowserOnly = $true }
& $completion @params
