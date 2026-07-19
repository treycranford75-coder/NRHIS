[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^\d{3}$')][string]$BuildNumber,
    [switch]$ForceExtract,
    [switch]$NoChain
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
$entry = Join-Path $buildFolder ("Apply-Build{0}.ps1" -f $BuildNumber)
$params = @{ RepositoryRoot = $repo }
if ($NoChain) { $params.NoChain = $true }
& $entry @params
# Legacy starter-name compatibility:
# Apply-Build BuildNumber.ps1
# Apply-Build$BuildNumber.ps1
