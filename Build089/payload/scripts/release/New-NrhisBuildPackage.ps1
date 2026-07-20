[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^\d{3}$')][string]$BuildNumber,
    [Parameter(Mandatory)][string]$SourceDirectory,
    [string]$OutputDirectory = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$source = (Resolve-Path $SourceDirectory).Path
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

$zip = Join-Path $OutputDirectory "NRHIS_Sprint2_Build${BuildNumber}_OneStep.zip"
$sha = "$zip.sha256"
Remove-Item $zip, $sha -Force -ErrorAction SilentlyContinue

Compress-Archive -Path (Join-Path $source '*') -DestinationPath $zip -CompressionLevel Optimal
$hash = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLowerInvariant()
"$hash  $(Split-Path $zip -Leaf)" | Set-Content $sha -Encoding ASCII

Write-Host "Created: $zip" -ForegroundColor Green
Write-Host "Created: $sha" -ForegroundColor Green
Write-Host "SHA-256: $hash" -ForegroundColor Green
