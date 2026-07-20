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
    $sourcePath = [System.IO.Path]::GetFullPath($_.FullName)
    $destinationPath = [System.IO.Path]::GetFullPath($dest)
    if (-not $sourcePath.Equals($destinationPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        Copy-Item $_.FullName $dest -Force
    }
}
python -m pytest tests/test_release_lifecycle_preflight_build080.py -q
if ($LASTEXITCODE -ne 0) { throw 'Build080 tests failed.' }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo 'scripts/release/Test-NrhisReleaseLifecycle.ps1') -RepositoryRoot $repo
if ($LASTEXITCODE -ne 0) { throw 'Build080 lifecycle preflight failed.' }
$branch = 'feature/sprint2-build080'
git switch -C $branch
git add -A
git commit -m 'Build080: add release lifecycle preflight gate'
git push --force-with-lease origin $branch
Write-Host 'Build080 applied and pushed.' -ForegroundColor Green
