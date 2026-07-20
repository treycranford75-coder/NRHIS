[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [switch]$NoChain,
    [switch]$NoArchive
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = (Resolve-Path $RepositoryRoot).Path
if (-not (Test-Path (Join-Path $repo '.git'))) { throw 'Run from the NRHIS repository root.' }
Set-Location $repo
$payload = Join-Path $PSScriptRoot 'payload'
Get-ChildItem $payload -Recurse -File | ForEach-Object {
    $relative = $_.FullName.Substring($payload.Length).TrimStart([char[]]@('\','/'))
    $dest = Join-Path $repo $relative
    New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force | Out-Null
    Copy-Item $_.FullName $dest -Force
}
$completionSource = Join-Path $PSScriptRoot 'Complete-Build077.ps1'
$completionDestination = Join-Path $repo 'Build077\Complete-Build077.ps1'

$sourcePath = [System.IO.Path]::GetFullPath($completionSource)
$destinationPath = [System.IO.Path]::GetFullPath($completionDestination)

if (-not $sourcePath.Equals(
    $destinationPath,
    [System.StringComparison]::OrdinalIgnoreCase
)) {
    Copy-Item $completionSource $completionDestination -Force
}
else {
    Write-Host "Build077 completion wrapper already in place." `
        -ForegroundColor DarkGray
}
python -m pytest tests/test_release_completion_helper_build077.py -q
if ($LASTEXITCODE -ne 0) { throw 'Build077 tests failed.' }
$branch = 'feature/sprint2-build077'
git switch -C $branch
git add -A
git commit -m 'Build077: install canonical completion helper'
git push --force-with-lease origin $branch
Write-Host 'Build077 applied and pushed.' -ForegroundColor Green
