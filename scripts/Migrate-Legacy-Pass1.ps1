[CmdletBinding()]
param(
    [string]$SourcePath = "$env:USERPROFILE\Downloads\Upper_Nueces_Pass1_Calibration_Package_v2\pass1_upper_nueces"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Destination = Join-Path $RepoRoot "src\nrhis_calibration\legacy"

if (-not (Test-Path $SourcePath)) {
    throw "Legacy source folder was not found: $SourcePath"
}

New-Item -ItemType Directory -Force -Path $Destination | Out-Null

$FilesToCopy = @(
    "calibrate_pass1.py",
    "run_pass1.ps1",
    "Run_Pass1.bat",
    "README.txt",
    "pass1_output.zip"
)

foreach ($Name in $FilesToCopy) {
    $SourceFile = Join-Path $SourcePath $Name
    if (Test-Path $SourceFile) {
        Copy-Item $SourceFile $Destination -Force
        Write-Host "Copied $Name" -ForegroundColor Green
    }
    else {
        Write-Warning "Not found and skipped: $SourceFile"
    }
}

$OutputSource = Join-Path $SourcePath "pass1_output"
$OutputDestination = Join-Path $Destination "pass1_output"
if (Test-Path $OutputSource) {
    Copy-Item $OutputSource $OutputDestination -Recurse -Force
    Write-Host "Copied pass1_output directory" -ForegroundColor Green
}

$ManifestPath = Join-Path $Destination "MIGRATION_MANIFEST.txt"
@(
    "NRHIS legacy migration",
    "Migration time: $(Get-Date -Format o)",
    "Source: $SourcePath",
    "Destination: $Destination",
    "Method: copy only; source not modified"
) | Set-Content -Path $ManifestPath -Encoding UTF8

Write-Host "Legacy Pass 1 package preserved in $Destination" -ForegroundColor Cyan
Write-Host "Review with: git status" -ForegroundColor Yellow
