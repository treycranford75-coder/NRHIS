[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PayloadRoot,

    [string[]]$AdditionalFiles = @(),

    [string[]]$RequiredFiles = @()
)

$ErrorActionPreference = "Stop"

$expectedFiles = @(
    & .\scripts\release\Get-NrhisBuildPayloadFiles.ps1 `
        -PayloadRoot $PayloadRoot `
        -AdditionalFiles $AdditionalFiles
)

foreach ($requiredFile in $RequiredFiles) {
    $normalized = $requiredFile.Replace("\", "/")

    if (-not (Test-Path $normalized)) {
        throw "Required permanent workflow file is missing: $normalized"
    }

    $requiredStatus = git status --porcelain -- $normalized

    if ($requiredStatus -and $normalized -notin $expectedFiles) {
        $expectedFiles += $normalized
    }
}

$expectedFiles = @($expectedFiles | Sort-Object -Unique)

foreach ($file in $expectedFiles) {
    if (-not (Test-Path $file)) {
        throw "Expected build file is missing from the working tree: $file"
    }
}

git add -- $expectedFiles
if ($LASTEXITCODE -ne 0) {
    throw "Unable to stage the complete build payload."
}

git diff --cached --check
if ($LASTEXITCODE -ne 0) {
    throw "Staged whitespace validation failed."
}

& .\scripts\release\Test-NrhisBuildChangeSet.ps1 `
    -ExpectedFiles $expectedFiles

Write-Host ""
Write-Host "Complete build payload staged and verified." -ForegroundColor Green
Write-Host "Expected file count: $($expectedFiles.Count)"

return $expectedFiles
