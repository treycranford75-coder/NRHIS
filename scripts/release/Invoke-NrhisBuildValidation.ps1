[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PayloadRoot,

    [int]$MinimumCoverage = 80
)

$ErrorActionPreference = "Stop"

& .\scripts\release\Test-NrhisPayloadConsistency.ps1 `
    -PayloadRoot $PayloadRoot

& .\scripts\release\Invoke-NrhisCiParity.ps1 `
    -MinimumCoverage $MinimumCoverage

Write-Host ""
Write-Host "Build validation completed successfully." -ForegroundColor Green
