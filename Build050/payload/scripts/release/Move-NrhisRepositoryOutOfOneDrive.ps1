[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$SourceRepository,
    [string]$DestinationRepository = "C:\GitHub\NRHIS",
    [Parameter(Mandatory)][string]$BuildNumber,
    [switch]$NoChain
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$source = (Resolve-Path $SourceRepository).Path
if ($source -notmatch '(?i)[\\/]OneDrive[\\/]') {
    return [ordered]@{ migrated = $false; repository = $source }
}

Write-Host "OneDrive-managed repository detected: $source" -ForegroundColor Yellow
Write-Host "Migrating NRHIS execution to: $DestinationRepository" -ForegroundColor Cyan

$destinationParent = Split-Path $DestinationRepository -Parent
New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null

if (-not (Test-Path (Join-Path $DestinationRepository '.git'))) {
    if (Test-Path $DestinationRepository) {
        $existing = Get-ChildItem $DestinationRepository -Force -ErrorAction SilentlyContinue
        if ($existing) { throw "Migration destination exists and is not an empty Git repository: $DestinationRepository" }
    }
    & git clone "https://github.com/treycranford75-coder/NRHIS.git" $DestinationRepository
    if ($LASTEXITCODE -ne 0) { throw "Unable to clone NRHIS to $DestinationRepository." }
}

Push-Location $DestinationRepository
try {
    $env:GIT_TERMINAL_PROMPT = "0"
    & git switch develop
    if ($LASTEXITCODE -ne 0) {
        & git switch --track origin/develop
        if ($LASTEXITCODE -ne 0) { throw "Unable to switch migrated repository to develop." }
    }
    & git fetch origin --tags
    if ($LASTEXITCODE -ne 0) { throw "Unable to fetch migrated repository." }
    & git pull --ff-only origin develop
    if ($LASTEXITCODE -ne 0) { throw "Unable to fast-forward migrated repository." }

    $fileName = "NRHIS_Sprint2_Build${BuildNumber}_OneStep.zip"
    foreach ($name in @($fileName, "$fileName.sha256")) {
        $sourceFile = Join-Path $source $name
        if (-not (Test-Path $sourceFile -PathType Leaf)) { throw "Migration source file missing: $sourceFile" }
        Copy-Item $sourceFile (Join-Path $DestinationRepository $name) -Force
    }

    $handoffRoot = Join-Path $HOME "NRHIS-Release-Evidence\Build$BuildNumber\repository-migration"
    New-Item -ItemType Directory -Path $handoffRoot -Force | Out-Null
    $receipt = Join-Path $handoffRoot "repository-migration-receipt.json"
    [ordered]@{
        schema_version = 1
        build = $BuildNumber
        migrated_utc = [DateTime]::UtcNow.ToString('o')
        source_repository = $source
        destination_repository = $DestinationRepository
        reason = "Protect Git internal files from OneDrive synchronization and deletion prompts."
        no_prune = $true
    } | ConvertTo-Json -Depth 5 | Set-Content $receipt -Encoding utf8

    Write-Host "Repository migration receipt: $receipt" -ForegroundColor Green
    Write-Host "Continuing Build$BuildNumber from the non-OneDrive repository." -ForegroundColor Green

    $starter = Join-Path $DestinationRepository "scripts\release\Start-NrhisBuild.ps1"
    if (-not (Test-Path $starter -PathType Leaf)) { throw "Migrated repository starter missing: $starter" }
    $arguments = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $starter,
        "-BuildNumber", $BuildNumber
    )
    if ($NoChain) { $arguments += "-NoChain" }
    & powershell.exe @arguments
    if ($LASTEXITCODE -ne 0) { throw "Migrated Build$BuildNumber starter failed with exit code $LASTEXITCODE." }
} finally {
    Pop-Location
}

return [ordered]@{ migrated = $true; repository = $DestinationRepository }
