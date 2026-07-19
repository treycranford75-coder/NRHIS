[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ReleaseNotesFile
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ReleaseNotesFile)) {
    throw "Release notes file not found: $ReleaseNotesFile"
}

$content = Get-Content $ReleaseNotesFile -Raw
Set-Clipboard -Value $content

Write-Host "Markdown release notes copied to the clipboard." -ForegroundColor Green
