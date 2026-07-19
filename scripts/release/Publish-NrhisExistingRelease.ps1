[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Tag,

    [Parameter(Mandatory = $true)]
    [string]$ReleaseTitle,

    [Parameter(Mandatory = $true)]
    [string]$ReleaseNotesFile,

    [string]$TargetBranch = "develop"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ReleaseNotesFile)) {
    throw "Release notes file not found: $ReleaseNotesFile"
}

$repository = & .\scripts\release\Get-NrhisGitHubRepository.ps1

$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($null -eq $gh) {
    throw "GitHub CLI is required. Run Initialize-NrhisGitHubCli.ps1 first."
}

gh auth status *> $null
if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI is not authenticated."
}

git show-ref --tags --verify --quiet "refs/tags/$Tag"
if ($LASTEXITCODE -ne 0) {
    throw "Local tag not found: $Tag"
}

git ls-remote --exit-code --tags origin "refs/tags/$Tag" *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Remote tag not found: $Tag"
}

gh release view $Tag --repo $repository *> $null
if ($LASTEXITCODE -eq 0) {
    throw "A GitHub release already exists for tag $Tag."
}

gh release create $Tag `
    --repo $repository `
    --title $ReleaseTitle `
    --notes-file $ReleaseNotesFile `
    --prerelease `
    --target $TargetBranch

if ($LASTEXITCODE -ne 0) {
    throw "GitHub release publication failed."
}

Write-Host "GitHub pre-release published: $Tag" -ForegroundColor Green
