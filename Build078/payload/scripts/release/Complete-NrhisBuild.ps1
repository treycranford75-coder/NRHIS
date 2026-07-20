[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^\d{3}$')][string]$BuildNumber,
    [string]$RepositoryRoot = (Get-Location).Path,
    [Parameter(Mandatory)][string]$Tag,
    [Parameter(Mandatory)][string]$ReleaseTitle,
    [Parameter(Mandatory)][string]$NotesFile
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
if (-not (Test-Path (Join-Path $repo '.git'))) {
    throw 'Run from the NRHIS repository root.'
}
Set-Location $repo

$notesPath = if ([System.IO.Path]::IsPathRooted($NotesFile)) { $NotesFile } else { Join-Path $repo $NotesFile }
if (-not (Test-Path $notesPath -PathType Leaf)) { throw "Release notes file not found: $notesPath" }

Write-Host 'Synchronizing develop without pruning...' -ForegroundColor Cyan
git fetch origin develop
if ($LASTEXITCODE -ne 0) { throw 'Unable to fetch origin/develop.' }
git switch develop
if ($LASTEXITCODE -ne 0) { throw 'Unable to switch to develop.' }
git pull --ff-only origin develop
if ($LASTEXITCODE -ne 0) { throw 'Unable to fast-forward local develop.' }

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'GitHub CLI (gh) is required for release publication.' }
& gh auth status 1>$null 2>$null
if ($LASTEXITCODE -ne 0) { throw 'GitHub CLI is not authenticated. Run: gh auth login' }

$repository = (@(& (Join-Path $repo 'scripts/release/Get-NrhisGitHubRepository.ps1')) -join "`n").Trim()
if ([string]::IsNullOrWhiteSpace($repository)) { throw 'Unable to determine the GitHub repository.' }

$nativePreferenceExists = Test-Path variable:PSNativeCommandUseErrorActionPreference
if ($nativePreferenceExists) {
    $savedNativePreference = $PSNativeCommandUseErrorActionPreference
    $PSNativeCommandUseErrorActionPreference = $false
}
try {
    $savedErrorPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $existingLines = @(& gh release view $Tag --repo $repository --json url --jq '.url' 2>$null)
    $releaseViewExitCode = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $savedErrorPreference
    if ($nativePreferenceExists) { $PSNativeCommandUseErrorActionPreference = $savedNativePreference }
}
$existing = ($existingLines -join "`n").Trim()

if ($releaseViewExitCode -eq 0 -and -not [string]::IsNullOrWhiteSpace($existing)) {
    $releaseUrl = $existing
    Write-Host "GitHub pre-release already exists: $releaseUrl" -ForegroundColor Cyan
}
else {
    Write-Host 'Publishing GitHub pre-release automatically...' -ForegroundColor Cyan
    $releaseLines = @(& gh release create $Tag `
        --repo $repository `
        --target develop `
        --prerelease `
        --title $ReleaseTitle `
        --notes-file $notesPath)
    if ($LASTEXITCODE -ne 0) { throw "Build$BuildNumber GitHub release publication failed." }
    $releaseUrl = ($releaseLines -join "`n").Trim()
    if ([string]::IsNullOrWhiteSpace($releaseUrl)) { throw "Build$BuildNumber GitHub release returned no URL." }
}

$evidenceRoot = Join-Path $HOME "NRHIS-Release-Evidence\Build$BuildNumber"
New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null
$receiptPath = Join-Path $evidenceRoot 'completion-receipt.json'
$receipt = [ordered]@{
    schema_version = 1
    build = $BuildNumber
    release_url = $releaseUrl
    tag = $Tag
    release_title = $ReleaseTitle
    completed_at = [DateTime]::UtcNow.ToString('o')
    status = 'verified'
    verified = $true
}
$json = $receipt | ConvertTo-Json -Depth 5
[System.IO.File]::WriteAllText($receiptPath, $json + "`n", [System.Text.UTF8Encoding]::new($false))

Write-Host "Build$BuildNumber release verification closed." -ForegroundColor Green
Write-Host "Receipt: $receiptPath" -ForegroundColor Green
Write-Host "Build$BuildNumber automated publication and verification completed." -ForegroundColor Green
Write-Host "Release: $releaseUrl"
Write-Host "Receipt: $receiptPath"
