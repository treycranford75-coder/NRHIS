[CmdletBinding()]
param(
    [string]$ExpectedRepository = "treycranford75-coder/NRHIS",
    [string]$ExpectedBranch = "develop",
    [switch]$RequireGitHubCli
)

$ErrorActionPreference = "Stop"

function Add-Check {
    param(
        [System.Collections.Generic.List[object]]$Results,
        [string]$Name,
        [bool]$Passed,
        [string]$Detail
    )

    $Results.Add(
        [pscustomobject]@{
            Check = $Name
            Passed = $Passed
            Detail = $Detail
        }
    )
}

$results = [System.Collections.Generic.List[object]]::new()

$git = Get-Command git -ErrorAction SilentlyContinue
Add-Check $results "Git installed" ($null -ne $git) (
    if ($git) { $git.Source } else { "git not found" }
)

$python = Get-Command python -ErrorAction SilentlyContinue
Add-Check $results "Python installed" ($null -ne $python) (
    if ($python) { $python.Source } else { "python not found" }
)

$repository = ""
if ($git) {
    try {
        $repository = & .\scripts\release\Get-NrhisGitHubRepository.ps1
        Add-Check $results "Repository match" ($repository -eq $ExpectedRepository) $repository
    }
    catch {
        Add-Check $results "Repository match" $false $_.Exception.Message
    }

    $branch = (git branch --show-current).Trim()
    Add-Check $results "Branch match" ($branch -eq $ExpectedBranch) $branch

    $status = git status --porcelain
    Add-Check $results "Working tree clean" (-not [bool]$status) (
        if ($status) { "working tree has changes" } else { "clean" }
    )
}

$gh = Get-Command gh -ErrorAction SilentlyContinue
Add-Check $results "GitHub CLI installed" ($null -ne $gh) (
    if ($gh) { $gh.Source } else { "gh not found" }
)

$ghAuthenticated = $false
if ($gh) {
    gh auth status *> $null
    $ghAuthenticated = $LASTEXITCODE -eq 0
    Add-Check $results "GitHub CLI authenticated" $ghAuthenticated (
        if ($ghAuthenticated) { "authenticated" } else { "not authenticated" }
    )
}
else {
    Add-Check $results "GitHub CLI authenticated" $false "gh not installed"
}

$results | Format-Table -AutoSize

$requiredFailures = @(
    $results | Where-Object {
        $_.Check -in @(
            "Git installed",
            "Python installed",
            "Repository match",
            "Branch match",
            "Working tree clean"
        ) -and -not $_.Passed
    }
)

if ($RequireGitHubCli) {
    $requiredFailures += @(
        $results | Where-Object {
            $_.Check -in @(
                "GitHub CLI installed",
                "GitHub CLI authenticated"
            ) -and -not $_.Passed
        }
    )
}

if ($requiredFailures.Count -gt 0) {
    throw "Release environment preflight failed."
}

Write-Host ""
Write-Host "NRHIS release environment preflight passed." -ForegroundColor Green
