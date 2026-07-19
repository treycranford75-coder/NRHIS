[CmdletBinding()]
param(
    [string]$Branch = "develop"
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

Invoke-Checked "Switch to $Branch" {
    git switch $Branch
}

Invoke-Checked "Fetch origin without pruning" {
    git fetch origin --no-prune
}

Invoke-Checked "Fast-forward $Branch without pruning" {
    git pull --ff-only --no-prune origin $Branch
}

Write-Host ""
Write-Host "$Branch is synchronized without remote-reference pruning." -ForegroundColor Green
