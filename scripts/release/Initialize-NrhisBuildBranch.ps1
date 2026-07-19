[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BaseBranch,

    [Parameter(Mandatory = $true)]
    [string]$FeatureBranch
)

$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param(
        [string]$Description,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Description" -ForegroundColor Cyan
    & $Command

    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

Invoke-Checked "Switch to $BaseBranch" {
    git switch $BaseBranch
}

Invoke-Checked "Fetch origin without pruning" {
    git fetch origin --no-prune
}

Invoke-Checked "Fast-forward $BaseBranch without pruning" {
    git pull --ff-only --no-prune origin $BaseBranch
}

$localFeature = git branch --list $FeatureBranch
if ($localFeature) {
    Invoke-Checked "Switch to existing $FeatureBranch" {
        git switch $FeatureBranch
    }
}
else {
    Invoke-Checked "Create $FeatureBranch from $BaseBranch" {
        git switch -c $FeatureBranch $BaseBranch
    }
}

Write-Host ""
Write-Host "Build branch initialized safely." -ForegroundColor Green
Write-Host "Base: $BaseBranch"
Write-Host "Feature: $FeatureBranch"
