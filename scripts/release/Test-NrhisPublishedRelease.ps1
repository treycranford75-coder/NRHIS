[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Tag,

    [Parameter(Mandatory = $true)]
    [string]$ExpectedTitle,

    [Parameter(Mandatory = $true)]
    [string]$ExpectedNotesFile,

    [switch]$RequirePrerelease = $true
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ExpectedNotesFile)) {
    throw "Expected release-notes file not found: $ExpectedNotesFile"
}

$repository = & .\scripts\release\Get-NrhisGitHubRepository.ps1
$apiUrl = "https://api.github.com/repos/$repository/releases/tags/$Tag"

$headers = @{
    Accept = "application/vnd.github+json"
    "User-Agent" = "NRHIS-Release-Verifier"
    "X-GitHub-Api-Version" = "2022-11-28"
}

try {
    $release = Invoke-RestMethod `
        -Uri $apiUrl `
        -Headers $headers `
        -Method Get
}
catch {
    throw "Unable to retrieve published release for tag $Tag. $($_.Exception.Message)"
}

$expectedNotes = (Get-Content $ExpectedNotesFile -Raw).Trim()
$actualNotes = ([string]$release.body).Trim()

$checks = [ordered]@{
    tag_name = ([string]$release.tag_name -eq $Tag)
    title = ([string]$release.name -eq $ExpectedTitle)
    prerelease = (
        if ($RequirePrerelease) {
            [bool]$release.prerelease
        }
        else {
            $true
        }
    )
    draft_false = (-not [bool]$release.draft)
    notes_exact = ($actualNotes -eq $expectedNotes)
    published_url_present = (-not [string]::IsNullOrWhiteSpace([string]$release.html_url))
}

$failedChecks = @(
    $checks.GetEnumerator() |
        Where-Object { -not $_.Value } |
        ForEach-Object { $_.Key }
)

$evidenceRoot = & .\scripts\release\Get-NrhisReleaseEvidenceRoot.ps1
$safeTag = $Tag -replace '[^A-Za-z0-9._-]', '_'
$evidencePath = Join-Path $evidenceRoot "${safeTag}_release_verification.json"

$evidence = [ordered]@{
    schema_version = 1
    verified_at_utc = [DateTimeOffset]::UtcNow.ToString("o")
    repository = $repository
    expected = [ordered]@{
        tag = $Tag
        title = $ExpectedTitle
        prerelease = [bool]$RequirePrerelease
        notes_file = (Resolve-Path $ExpectedNotesFile).Path
    }
    actual = [ordered]@{
        id = $release.id
        tag = $release.tag_name
        title = $release.name
        prerelease = $release.prerelease
        draft = $release.draft
        html_url = $release.html_url
        published_at = $release.published_at
        target_commitish = $release.target_commitish
    }
    checks = $checks
    passed = ($failedChecks.Count -eq 0)
    failed_checks = $failedChecks
}

$evidence |
    ConvertTo-Json -Depth 8 |
    Set-Content -Path $evidencePath -Encoding utf8

Write-Host ""
Write-Host "Release verification evidence:" -ForegroundColor Cyan
Write-Host $evidencePath

$checks.GetEnumerator() | ForEach-Object {
    $status = if ($_.Value) { "PASS" } else { "FAIL" }
    Write-Host ("{0,-24} {1}" -f $_.Key, $status)
}

if ($failedChecks.Count -gt 0) {
    throw "Published release verification failed: $($failedChecks -join ', ')"
}

Write-Host ""
Write-Host "Published release verification passed." -ForegroundColor Green
Write-Host "Release: $($release.html_url)"
