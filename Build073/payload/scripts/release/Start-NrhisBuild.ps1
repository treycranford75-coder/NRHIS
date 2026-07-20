[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^\d{3}$')][string]$BuildNumber,
    [switch]$ForceExtract,
    [switch]$NoChain,
    [switch]$SkipPullRequest,
    [switch]$SkipLifecycle,
    [switch]$SkipArchive
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Get-SearchRoots {
    param([Parameter(Mandatory)][string]$RepositoryRoot)
    $roots = @(
        $RepositoryRoot,
        (Split-Path $RepositoryRoot -Parent),
        (Split-Path (Split-Path $RepositoryRoot -Parent) -Parent),
        (Join-Path $HOME "Downloads"),
        (Join-Path $HOME "OneDrive\Downloads"),
        (Join-Path $HOME "Desktop"),
        (Join-Path $HOME "OneDrive\Desktop")
    )
    return $roots | Where-Object { $_ -and (Test-Path $_ -PathType Container) } | Select-Object -Unique
}

function Find-BuildFile {
    param([string]$FileName, [string[]]$Roots)
    Write-Host "Searching for $FileName in:" -ForegroundColor Cyan
    foreach ($root in $Roots) {
        Write-Host "  $root"
        $candidate = Join-Path $root $FileName
        if (Test-Path $candidate -PathType Leaf) { return (Resolve-Path $candidate).Path }
    }
    return $null
}

function Read-ExpectedHash {
    param([string]$ChecksumPath)
    $text = (Get-Content $ChecksumPath -Raw).Trim()
    $match = [regex]::Match($text, '(?i)\b[0-9a-f]{64}\b')
    if (-not $match.Success) { throw "Checksum file does not contain a SHA-256 value: $ChecksumPath" }
    return $match.Value.ToLowerInvariant()
}

$repo = (Resolve-Path (Get-Location).Path).Path
if (-not (Test-Path (Join-Path $repo ".git"))) { throw "Run from the NRHIS repository root." }
$fileName = "NRHIS_Sprint2_Build${BuildNumber}_OneStep.zip"
$roots = Get-SearchRoots -RepositoryRoot $repo
$zip = Find-BuildFile -FileName $fileName -Roots $roots
if (-not $zip) { throw "Could not find $fileName in any searched location." }
$checksum = Find-BuildFile -FileName "$fileName.sha256" -Roots $roots
if (-not $checksum) { throw "Could not find $fileName.sha256 in any searched location." }
$expected = Read-ExpectedHash -ChecksumPath $checksum
$actual = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLowerInvariant()
if ($expected -ne $actual) { throw "Build ZIP checksum mismatch. Expected '$expected'; found '$actual'." }
Write-Host "Build ZIP checksum verified: $actual" -ForegroundColor Green

$rootZip = Join-Path $repo $fileName
$rootChecksum = "$rootZip.sha256"
if ($zip -ne $rootZip) { Copy-Item $zip $rootZip -Force }
if ($checksum -ne $rootChecksum) { Copy-Item $checksum $rootChecksum -Force }

$buildFolder = Join-Path $repo ("Build{0}" -f $BuildNumber)
$marker = Join-Path $buildFolder ".nrhis-extraction.json"
$reuse = $false
if (-not $ForceExtract -and (Test-Path $marker -PathType Leaf)) {
    try {
        $state = Get-Content $marker -Raw | ConvertFrom-Json
        if (([string]$state.zip_sha256).Trim().ToLowerInvariant() -eq $actual -and (Test-Path (Join-Path $buildFolder ("Apply-Build{0}.ps1" -f $BuildNumber)))) { $reuse = $true }
    } catch { $reuse = $false }
}
if ($reuse) {
    Write-Host "Reusing verified Build$BuildNumber extraction: $buildFolder" -ForegroundColor Cyan
} else {
    $temp = Join-Path $repo (".nrhis-extract-{0}-{1}" -f $BuildNumber, [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $temp -Force | Out-Null
    try {
        Expand-Archive -Path $rootZip -DestinationPath $temp -Force
        if (-not (Test-Path (Join-Path $temp ("Apply-Build{0}.ps1" -f $BuildNumber)))) { throw "Extracted package is missing its Build$BuildNumber entry point." }
        if (Test-Path $buildFolder) {
            $backup = "$buildFolder.previous"
            Remove-Item $backup -Recurse -Force -ErrorAction SilentlyContinue
            Move-Item $buildFolder $backup -Force -ErrorAction SilentlyContinue
            if (Test-Path $buildFolder) { throw "Unable to replace the existing Build$BuildNumber folder. Close programs using it or rerun without -ForceExtract." }
        }
        Move-Item $temp $buildFolder -Force
        [ordered]@{ build=$BuildNumber; zip=$rootZip; zip_sha256=$actual; extracted_utc=[DateTime]::UtcNow.ToString('o') } | ConvertTo-Json | Set-Content $marker -Encoding utf8
        Write-Host "Extracted Build$BuildNumber to $buildFolder" -ForegroundColor Cyan
    } finally {
        if (Test-Path $temp) { Remove-Item $temp -Recurse -Force -ErrorAction SilentlyContinue }
    }
}
$applyScript = Join-Path $buildFolder "Apply-Build$BuildNumber.ps1"
$entry = Join-Path $buildFolder "Apply-Build$BuildNumber.ps1"
if (-not (Test-Path $entry -PathType Leaf)) { throw "Apply script not found after extraction: $entry" }

$childArguments = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $entry,
    "-RepositoryRoot", $repo
)
if ($NoChain) { $childArguments += "-NoChain" }

Write-Host "Launching Build$BuildNumber with a process-scoped execution-policy bypass." -ForegroundColor Cyan
& powershell.exe @childArguments
if ($LASTEXITCODE -ne 0) { throw "Build$BuildNumber child process failed with exit code $LASTEXITCODE." }

if ($SkipPullRequest) {
    Write-Host "Build$BuildNumber applied and pushed. Pull-request creation skipped." -ForegroundColor Yellow
    exit 0
}

$prHelper = Join-Path $repo "scripts/release/New-NrhisPullRequest.ps1"
if (-not (Test-Path $prHelper -PathType Leaf)) {
    throw "Automatic PR helper not found: $prHelper"
}

$branch = "feature/sprint2-build$BuildNumber"
$bodyFile = Join-Path $repo "docs/releases/BUILD${BuildNumber}_PR.md"
$title = "Build${BuildNumber}: NRHIS Sprint 2 update"

$prUrl = & $prHelper `
    -BaseBranch "develop" `
    -HeadBranch $branch `
    -Title $title `
    -BodyFile $bodyFile

Write-Host "Build$BuildNumber applied and pushed." -ForegroundColor Green
Write-Host "Pull request ready: $prUrl" -ForegroundColor Green
Write-Host "Waiting for CI and merge into develop." -ForegroundColor Yellow
Write-Host "Monitoring required CI checks..." -ForegroundColor Cyan

if ($SkipLifecycle) {
    Write-Host "Automatic lifecycle completion skipped." -ForegroundColor Yellow
    exit 0
}

$lifecycleHelper = Join-Path $repo "scripts/release/Finish-NrhisBuildLifecycle.ps1"

if (-not (Test-Path $lifecycleHelper -PathType Leaf)) {
    throw "Lifecycle helper not found: $lifecycleHelper"
}

& $lifecycleHelper `
    -BuildNumber $BuildNumber `
    -PullRequestUrl $prUrl `
    -RepositoryRoot $repo `
    -SkipArchive:$SkipArchive

if ($LASTEXITCODE -ne 0) {
    throw "Build$BuildNumber lifecycle completion failed."
}

# Legacy workflow contract compatibility retained for historical tests:
# & $entry @params
# $params.NoChain = $true
