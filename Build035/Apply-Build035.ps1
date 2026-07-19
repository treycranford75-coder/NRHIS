[CmdletBinding()]
param([string]$RepositoryRoot = (Get-Location).Path)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
if (-not (Test-Path (Join-Path $repo ".git"))) { throw "Run from the NRHIS repository root." }
Set-Location $repo

$branch = "feature/sprint2-build035"
$current = (git branch --show-current).Trim()
if ($current -eq "develop") {
    git fetch origin --no-prune
    git pull --ff-only --no-prune origin develop
    git switch -c $branch
} elseif ($current -ne $branch) {
    throw "Build035 must run on develop or $branch. Current branch: $current"
}

$payload = Join-Path $PSScriptRoot "payload"
Get-ChildItem $payload -Recurse -File | ForEach-Object {
    $relative = $_.FullName.Substring($payload.Length).TrimStart([IO.Path]::DirectorySeparatorChar)
    $target = Join-Path $repo $relative
    New-Item -ItemType Directory -Path (Split-Path $target) -Force | Out-Null
    Copy-Item $_.FullName $target -Force
    $sourceHash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
    $targetHash = (Get-FileHash $target -Algorithm SHA256).Hash
    if ($sourceHash -ne $targetHash) { throw "Payload consistency failure: $relative" }
}

$parserErrors = @()
Get-ChildItem (Join-Path $repo "scripts") -Recurse -Filter "*.ps1" -File | ForEach-Object {
    $tokens = $null; $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($_.FullName, [ref]$tokens, [ref]$errors) | Out-Null
    if ($errors.Count -gt 0) { $parserErrors += $errors }
}
if ($parserErrors.Count -gt 0) { throw ($parserErrors | Out-String) }
Write-Host "PowerShell syntax validation passed." -ForegroundColor Green

if (Get-Command ruff -ErrorAction SilentlyContinue) { ruff check .; if ($LASTEXITCODE -ne 0) { throw "Ruff failed." } }
if (Get-Command pytest -ErrorAction SilentlyContinue) { pytest; if ($LASTEXITCODE -ne 0) { throw "Pytest failed." } }

git diff --check
if ($LASTEXITCODE -ne 0) { throw "Whitespace validation failed." }

git add --all
if (-not (git diff --cached --quiet)) {
    git commit -m "Build035: close release verification and index evidence"
    git push -u origin $branch
} else {
    Write-Host "No staged changes; payload-authoritative rerun is already applied."
}
Write-Host "Open PR: $branch -> develop" -ForegroundColor Cyan
