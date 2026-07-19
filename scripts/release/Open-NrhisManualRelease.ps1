[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Tag,

    [Parameter(Mandatory = $true)]
    [string]$ReleaseTitle,

    [Parameter(Mandatory = $true)]
    [string]$ReleaseNotesFile
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ReleaseNotesFile)) {
    throw "Release notes file not found: $ReleaseNotesFile"
}

$repository = & .\scripts\release\Get-NrhisGitHubRepository.ps1
$encodedTag = [uri]::EscapeDataString($Tag)
$encodedTitle = [uri]::EscapeDataString($ReleaseTitle)
$releaseUrl = "https://github.com/$repository/releases/new?tag=$encodedTag&title=$encodedTitle"

Start-Process $releaseUrl
Start-Sleep -Seconds 2

Get-Content $ReleaseNotesFile -Raw | Set-Clipboard

Write-Host ""
Write-Host "Manual release page opened." -ForegroundColor Green
Write-Host "Release tag: $Tag"
Write-Host "Release title: $ReleaseTitle"
Write-Host "Release notes copied to clipboard AFTER the browser opened." -ForegroundColor Green
Write-Host "Paste into the GitHub Release notes field with Ctrl+V."
