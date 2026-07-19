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

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BodyFile)) {
    throw "Pull-request body file not found: $BodyFile"
}

$repository = & .\scripts\release\Get-NrhisGitHubRepository.ps1
$compareUrl = "https://github.com/$repository/compare/${BaseBranch}...${HeadBranch}?expand=1"

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

gh pr create `
    --repo $repository `
    --base $BaseBranch `
    --head $HeadBranch `
    --title $Title `
    --body-file $BodyFile

if ($LASTEXITCODE -ne 0) {
    throw "GitHub pull-request creation failed."
}
