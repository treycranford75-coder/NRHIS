[CmdletBinding()]
param([string]$RepositoryRoot = (Get-Location).Path)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
if (-not (Test-Path (Join-Path $repo ".git"))) { throw "Run from the NRHIS repository root." }
Set-Location $repo

$build = "036"
$branch = "feature/sprint2-build$build"
$current = (git branch --show-current).Trim()

if ($current -eq "develop") {
    git fetch origin --no-prune
    if ($LASTEXITCODE -ne 0) { throw "Git fetch failed." }
    git pull --ff-only --no-prune origin develop
    if ($LASTEXITCODE -ne 0) { throw "Git pull failed." }
    git switch -c $branch
    if ($LASTEXITCODE -ne 0) { throw "Unable to create $branch." }
} elseif ($current -ne $branch) {
    throw "Build$build must run on develop or $branch. Current branch: $current"
}

$payload = Join-Path $PSScriptRoot "payload"
if (-not (Test-Path $payload)) { throw "Build$build payload is missing." }

Get-ChildItem $payload -Recurse -File | ForEach-Object {
    $relative = $_.FullName.Substring($payload.Length).TrimStart([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
    $target = Join-Path $repo $relative
    New-Item -ItemType Directory -Path (Split-Path $target) -Force | Out-Null
    Copy-Item $_.FullName $target -Force
    $sourceHash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
    $targetHash = (Get-FileHash $target -Algorithm SHA256).Hash
    if ($sourceHash -ne $targetHash) { throw "Payload consistency failure: $relative" }
}

$parserErrors = @()
Get-ChildItem (Join-Path $repo "scripts") -Recurse -Filter "*.ps1" -File | ForEach-Object {
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($_.FullName, [ref]$tokens, [ref]$errors) | Out-Null
    if ($errors.Count -gt 0) { $parserErrors += $errors }
}
Get-ChildItem $PSScriptRoot -Filter "*.ps1" -File | ForEach-Object {
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($_.FullName, [ref]$tokens, [ref]$errors) | Out-Null
    if ($errors.Count -gt 0) { $parserErrors += $errors }
}
if ($parserErrors.Count -gt 0) { throw ($parserErrors | Out-String) }
Write-Host "PowerShell syntax validation passed." -ForegroundColor Green

if (Get-Command ruff -ErrorAction SilentlyContinue) {
    ruff check .
    if ($LASTEXITCODE -ne 0) { throw "Ruff failed." }
}

if (Get-Command pytest -ErrorAction SilentlyContinue) {
    $coverageArgs = @("--cov=src", "--cov-branch", "--cov-fail-under=80")
    pytest @coverageArgs
    if ($LASTEXITCODE -ne 0) { throw "Pytest or branch-coverage gate failed." }
}

git diff --check
if ($LASTEXITCODE -ne 0) { throw "Whitespace validation failed." }

git add --all
if (-not (git diff --cached --quiet)) {
    git commit -m "Build036: automate pre-release publication and verification closure"
    if ($LASTEXITCODE -ne 0) { throw "Commit failed." }
    git push -u origin $branch
    if ($LASTEXITCODE -ne 0) { throw "Push failed." }
} else {
    Write-Host "No staged changes; payload-authoritative rerun is already applied."
}

Write-Host "Open PR: $branch -> develop" -ForegroundColor Cyan
Write-Host "After merge, run .\Build036\Complete-Build036.ps1" -ForegroundColor Yellow
