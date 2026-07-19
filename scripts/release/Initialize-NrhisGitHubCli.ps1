[CmdletBinding()]
param(
    [switch]$Install,
    [switch]$Authenticate
)

$ErrorActionPreference = "Stop"

$gh = Get-Command gh -ErrorAction SilentlyContinue

if (($null -eq $gh) -and $Install) {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($null -eq $winget) {
        throw "GitHub CLI is not installed and winget is unavailable."
    }

    winget install --id GitHub.cli --exact --source winget
    if ($LASTEXITCODE -ne 0) {
        throw "GitHub CLI installation failed."
    }

    $env:Path = [System.Environment]::GetEnvironmentVariable(
        "Path",
        "Machine"
    ) + ";" + [System.Environment]::GetEnvironmentVariable(
        "Path",
        "User"
    )

    $gh = Get-Command gh -ErrorAction SilentlyContinue
}

if ($null -eq $gh) {
    Write-Warning "GitHub CLI is not installed."
    Write-Host "Run this script again with -Install to install it through winget."
    exit 1
}

Write-Host "GitHub CLI: $($gh.Source)"

gh auth status *> $null
$authenticated = $LASTEXITCODE -eq 0

if ((-not $authenticated) -and $Authenticate) {
    gh auth login --hostname github.com --git-protocol https --web
    if ($LASTEXITCODE -ne 0) {
        throw "GitHub CLI authentication failed."
    }

    gh auth status *> $null
    $authenticated = $LASTEXITCODE -eq 0
}

if (-not $authenticated) {
    Write-Warning "GitHub CLI is installed but not authenticated."
    Write-Host "Run this script again with -Authenticate."
    exit 1
}

Write-Host "GitHub CLI is installed and authenticated." -ForegroundColor Green
