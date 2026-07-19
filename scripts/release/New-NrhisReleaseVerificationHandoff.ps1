[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BuildNumber,

    [Parameter(Mandatory = $true)]
    [string]$Tag,

    [Parameter(Mandatory = $true)]
    [string]$ReleaseTitle,

    [Parameter(Mandatory = $true)]
    [string]$ReleaseNotesFile,

    [int]$TimeoutMinutes = 15
)

$ErrorActionPreference = "Stop"

$handoffRoot = & .\scripts\release\Get-NrhisHandoffRoot.ps1
$command = & .\scripts\release\Get-NrhisReleaseVerificationCommand.ps1 `
    -Tag $Tag `
    -ReleaseTitle $ReleaseTitle `
    -ReleaseNotesFile $ReleaseNotesFile `
    -TimeoutMinutes $TimeoutMinutes

$handoffPath = Join-Path `
    $handoffRoot `
    "Build${BuildNumber}_Release_Verification.md"

$evidenceRoot = & .\scripts\release\Get-NrhisReleaseEvidenceRoot.ps1
$safeTag = $Tag -replace '[^A-Za-z0-9._-]', '_'
$evidencePath = Join-Path `
    $evidenceRoot `
    "${safeTag}_release_verification.json"

$contents = @"
# NRHIS Build$BuildNumber Release Verification

## Release

- Tag: ``$Tag``
- Title: $ReleaseTitle
- Notes: ``$ReleaseNotesFile``

## After publishing

Run:

````powershell
$command
````

## Expected evidence

``$evidencePath``
"@

[System.IO.File]::WriteAllText(
    $handoffPath,
    $contents.TrimStart(),
    [System.Text.UTF8Encoding]::new($false)
)

Set-Clipboard -Value $command

Write-Host ""
Write-Host "Release-verification handoff created:" -ForegroundColor Green
Write-Host $handoffPath
Write-Host "Verification command copied to clipboard."
Write-Host "Expected evidence: $evidencePath"

return $handoffPath
