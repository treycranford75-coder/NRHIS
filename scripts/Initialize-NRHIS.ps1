[CmdletBinding()]
param(
    [switch]$SkipGit
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "Initializing NRHIS in $RepoRoot" -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found on PATH. Install Python 3.11 or newer, then rerun."
}

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -e ".[dev]"

if (-not $SkipGit) {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw "Git was not found on PATH. Install Git for Windows, then rerun with no changes."
    }

    if (-not (Test-Path ".git")) {
        git init
        git branch -M main
    }
}

Write-Host "Running tests..." -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" -m pytest

Write-Host "NRHIS foundation initialized successfully." -ForegroundColor Green
Write-Host "Next: run .\scripts\Migrate-Legacy-Pass1.ps1" -ForegroundColor Yellow
