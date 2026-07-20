[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d{3}$')]
    [string]$BuildNumber,

    [Parameter(Mandatory = $true)]
    [string]$RepositoryRoot
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'GitHub CLI is required to resolve the pull request automatically.'
}

$branch = "feature/sprint2-build$BuildNumber"
$url = @(& gh pr list --head $branch --state all --limit 1 --json url --jq '.[0].url' 2>$null) -join "`n"
$url = $url.Trim()

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($url)) {
    throw "No pull request found for branch $branch."
}

if ($url -notmatch '^https://github\.com/[^/]+/[^/]+/pull/\d+$') {
    throw "GitHub returned an invalid pull-request URL: $url"
}

Write-Output $url
