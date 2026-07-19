[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern("^\d{3}$")]
    [string]$BuildNumber,

    [string]$RepositoryRoot = (Get-Location).Path,

    [switch]$KeepInstallerArtifacts
)

$ErrorActionPreference = "Stop"

function Resolve-NrhisBuildZip {
    param(
        [string]$BuildNumber,
        [string]$RepositoryRoot
    )

    $fileName = "NRHIS_Sprint2_Build${BuildNumber}_OneStep.zip"
    $candidates = @(
        (Join-Path $RepositoryRoot $fileName),
        (Join-Path $HOME "Downloads\$fileName"),
        (Join-Path $HOME "OneDrive\Downloads\$fileName"),
        (Join-Path $HOME "Desktop\$fileName")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    throw "Could not find $fileName in the repository root, Downloads, OneDrive Downloads, or Desktop."
}

$repoRoot = (Resolve-Path $RepositoryRoot).Path
if (-not (Test-Path (Join-Path $repoRoot ".git"))) {
    throw "NRHIS repository root not found: $repoRoot"
}

$zipPath = Resolve-NrhisBuildZip `
    -BuildNumber $BuildNumber `
    -RepositoryRoot $repoRoot

$extractPath = Join-Path $repoRoot "Build$BuildNumber"
$applyScript = Join-Path $extractPath "Apply-Build$BuildNumber.ps1"

Write-Host "Repository: $repoRoot"
Write-Host "Build ZIP: $zipPath"
Write-Host "Extracting to: $extractPath"

if (Test-Path $extractPath) {
    Remove-Item $extractPath -Recurse -Force
}

Expand-Archive `
    -Path $zipPath `
    -DestinationPath $extractPath `
    -Force

if (-not (Test-Path $applyScript)) {
    throw "Apply script not found after extraction: $applyScript"
}

Set-Location $repoRoot

Write-Host ""
Write-Host "Starting Build$BuildNumber..." -ForegroundColor Cyan
& $applyScript

if ($LASTEXITCODE -ne 0) {
    throw "Build$BuildNumber application failed with exit code $LASTEXITCODE."
}

if (-not $KeepInstallerArtifacts) {
    Write-Host ""
    Write-Host "Installer artifacts retained until post-merge completion." -ForegroundColor Yellow
}
