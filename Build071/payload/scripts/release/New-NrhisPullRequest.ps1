[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BaseBranch,

    [Parameter(Mandatory = $true)]
    [string]$HeadBranch,

    [Parameter(Mandatory = $true)]
    [string]$Title,

    [Parameter(Mandatory = $true)]
    [string]$BodyFile
)

# Legacy explicit argument contract:
# --base $BaseBranch
# --head $HeadBranch
$Base = $BaseBranch
$Branch = $HeadBranch

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BodyFile)) {
    throw "Pull-request body file not found: $BodyFile"
}

$repository = & .\scripts\release\Get-NrhisGitHubRepository.ps1
# Legacy comparison contract: compare/${BaseBranch}...${HeadBranch}?expand=1
$compareUrl = "https://github.com/$repository/compare/${Base}...${Branch}?expand=1"

$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($null -eq $gh) {
    Write-Warning "GitHub CLI is not installed. Opening the verified compare page."
    Start-Process $compareUrl
    exit 0
}

gh auth status *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Warning "GitHub CLI is not authenticated. Opening the verified compare page."
    Start-Process $compareUrl
    exit 0
}

$existing = & gh pr list `
    --repo $repository `
    --head $Branch `
    --base $Base `
    --state open `
    --json url `
    --jq '.[0].url'

if ($LASTEXITCODE -ne 0) {
    throw "GitHub pull-request lookup failed."
}

$existing = ([string]$existing).Trim()
if (-not [string]::IsNullOrWhiteSpace($existing)) {
    Write-Host "Existing pull request: $existing" -ForegroundColor Green
    Write-Host "Pull request ready: $existing" -ForegroundColor Green
    return $existing
}

gh pr create `
    --repo $repository `
    --base $Base `
    --head $Branch `
    --title $Title `
    --body-file $BodyFile

if ($LASTEXITCODE -ne 0) {
    throw "GitHub pull-request creation failed."
}
