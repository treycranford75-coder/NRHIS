[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$EventId
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$EventRoot = Join-Path $RepoRoot "events\$EventId"

$Folders = @(
    "observations",
    "rainfall",
    "reservoirs",
    "calibration",
    "gis",
    "publications",
    "notebook",
    "archive"
)

New-Item -ItemType Directory -Force -Path $EventRoot | Out-Null
foreach ($Folder in $Folders) {
    New-Item -ItemType Directory -Force -Path (Join-Path $EventRoot $Folder) | Out-Null
}

@(
    "# $EventId",
    "",
    "Status: initialized",
    "Created: $(Get-Date -Format o)",
    "",
    "## Purpose",
    "",
    "Document the event purpose, period, basin areas, and responsible reviewer."
) | Set-Content -Path (Join-Path $EventRoot "README.md") -Encoding UTF8

Write-Host "Created event workspace: $EventRoot" -ForegroundColor Green
