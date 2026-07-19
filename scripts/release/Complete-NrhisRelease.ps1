[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BuildNumber,

    [Parameter(Mandatory = $true)]
    [string]$Tag,

    [Parameter(Mandatory = $true)]
    [string]$ReleaseTitle,

    [Parameter(Mandatory = $true)]
    [string]$ReleaseNotesFile,

    [string]$DevelopBranch = "develop",

    [int]$MinimumCoverage = 80,

    [string[]]$CleanupPaths = @()
)

$ErrorActionPreference = "Stop"

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Description,

        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Description" -ForegroundColor Cyan
    & $Command

    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

if (-not (Test-Path $ReleaseNotesFile)) {
    throw "Release notes file not found: $ReleaseNotesFile"
}

Invoke-CheckedCommand "Switch to $DevelopBranch" {
    git switch $DevelopBranch
}

Invoke-CheckedCommand "Update $DevelopBranch" {
    git pull --ff-only origin $DevelopBranch
}

$mergeCommit = (git rev-parse HEAD).Trim()
if (-not $mergeCommit) {
    throw "Unable to resolve the merged commit."
}

& .\scripts\release\Invoke-NrhisReleaseValidation.ps1 `
    -MinimumCoverage $MinimumCoverage

foreach ($cleanupPath in $CleanupPaths) {
    if (Test-Path $cleanupPath) {
        Remove-Item $cleanupPath -Recurse -Force
        Write-Host "Removed installer artifact: $cleanupPath"
    }
}

$status = git status --porcelain
if ($status) {
    Write-Host $status
    throw "Working tree is not clean after validation and cleanup."
}

$existingTag = git tag --list $Tag
if ($existingTag) {
    throw "Tag already exists locally: $Tag"
}

Invoke-CheckedCommand "Create annotated tag $Tag" {
    git tag -a $Tag -m "NRHIS Sprint 2 Build$BuildNumber release candidate"
}

$tagCommit = (git rev-list -n 1 $Tag).Trim()
if ($tagCommit -ne $mergeCommit) {
    throw "Tag $Tag points to $tagCommit instead of $mergeCommit."
}

Invoke-CheckedCommand "Push tag $Tag" {
    git push origin $Tag
}

$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($null -ne $gh) {
    gh auth status *> $null
}

if (($null -ne $gh) -and ($LASTEXITCODE -eq 0)) {
    Invoke-CheckedCommand "Publish GitHub pre-release" {
        gh release create $Tag `
            --title $ReleaseTitle `
            --notes-file $ReleaseNotesFile `
            --prerelease `
            --target $DevelopBranch
    }

    Write-Host ""
    Write-Host "Build$BuildNumber release published successfully." -ForegroundColor Green
    Write-Host "Merge commit: $mergeCommit"
    Write-Host "Tag: $Tag"
    exit 0
}

Write-Warning "GitHub CLI is unavailable or unauthenticated."
Write-Host "The tag was created and pushed successfully."
Start-Process "https://github.com/treycranford75-coder/NRHIS/releases/new"
