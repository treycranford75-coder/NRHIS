[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BuildNumber,

    [Parameter(Mandatory = $true)]
    [string]$BaseBranch,

    [Parameter(Mandatory = $true)]
    [string]$HeadBranch,

    [Parameter(Mandatory = $true)]
    [string]$PullRequestTitle,

    [Parameter(Mandatory = $true)]
    [string]$PullRequestBodyFile,

    [Parameter(Mandatory = $true)]
    [string]$ReleaseTag,

    [Parameter(Mandatory = $true)]
    [string]$ReleaseTitle,

    [Parameter(Mandatory = $true)]
    [string]$ReleaseNotesFile
)

$ErrorActionPreference = "Stop"

foreach ($requiredFile in @($PullRequestBodyFile, $ReleaseNotesFile)) {
    if (-not (Test-Path $requiredFile)) {
        throw "Required handoff file not found: $requiredFile"
    }
}

$repository = & .\scripts\release\Get-NrhisGitHubRepository.ps1
$compareUrl = "https://github.com/$repository/compare/${BaseBranch}...${HeadBranch}?expand=1"

$handoffDirectory = ".\handoff"
$handoffPath = Join-Path $handoffDirectory "Build${BuildNumber}_Operator_Handoff.md"
New-Item -ItemType Directory -Path $handoffDirectory -Force | Out-Null

$pullRequestBody = Get-Content $PullRequestBodyFile -Raw
$releaseNotes = Get-Content $ReleaseNotesFile -Raw

$handoff = @"
# NRHIS Build$BuildNumber Operator Handoff

## Pull request

- Base branch: `$BaseBranch`
- Compare branch: `$HeadBranch`
- Title: $PullRequestTitle
- Compare URL: $compareUrl

### Pull-request description

$pullRequestBody

## Release

- Tag: `$ReleaseTag`
- Title: $ReleaseTitle

### Release notes

$releaseNotes
"@

[System.IO.File]::WriteAllText(
    $handoffPath,
    $handoff.TrimEnd() + "`n",
    [System.Text.UTF8Encoding]::new($false)
)

Set-Clipboard -Value $pullRequestBody

Write-Host ""
Write-Host "Operator handoff created: $handoffPath" -ForegroundColor Green
Write-Host "Pull-request description copied to clipboard." -ForegroundColor Green
Write-Host "PR title: $PullRequestTitle"
Write-Host "Base: $BaseBranch"
Write-Host "Compare: $HeadBranch"
Write-Host "Release tag: $ReleaseTag"
Write-Host "Release title: $ReleaseTitle"

Start-Process $compareUrl
