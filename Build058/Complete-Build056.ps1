[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [switch]$BrowserOnly,
    [switch]$NoChain,
    [switch]$NoArchive
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$repo = (Resolve-Path $RepositoryRoot).Path
if (-not (Test-Path (Join-Path $repo ".git"))) { throw "Run from the NRHIS repository root." }
Set-Location $repo
if ((git branch --show-current).Trim() -ne "develop") { throw "Switch to develop after the Build056 PR is merged." }
$params = @{ RepositoryRoot = $repo }
if ($BrowserOnly) { $params.BrowserOnly = $true }
if ($NoChain) { $params.NoChain = $true }
if ($NoArchive) { $params.NoArchive = $true }
& (Join-Path $PSScriptRoot "Apply-Build056.ps1") @params
