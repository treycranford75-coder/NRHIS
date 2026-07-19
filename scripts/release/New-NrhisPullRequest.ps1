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

$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($null -eq $gh) {
    Write-Warning "GitHub CLI is not installed. Opening the GitHub compare page instead."
    $repositoryUrl = git remote get-url origin
    if ($repositoryUrl -match "github\.com[:/](.+?)(?:\.git)?$") {
        $slug = $Matches[1]
        Start-Process "https://github.com/$slug/compare/$BaseBranch...$HeadBranch?expand=1"
        exit 0
    }

    throw "Unable to determine the GitHub repository URL."
}

gh auth status *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Warning "GitHub CLI is not authenticated. Opening the GitHub compare page instead."
    $repositoryUrl = git remote get-url origin
    if ($repositoryUrl -match "github\.com[:/](.+?)(?:\.git)?$") {
        $slug = $Matches[1]
        Start-Process "https://github.com/$slug/compare/$BaseBranch...$HeadBranch?expand=1"
        exit 0
    }

    throw "Unable to determine the GitHub repository URL."
}

gh pr create `
    --base $BaseBranch `
    --head $HeadBranch `
    --title $Title `
    --body-file $BodyFile

if ($LASTEXITCODE -ne 0) {
    throw "GitHub pull-request creation failed."
}
