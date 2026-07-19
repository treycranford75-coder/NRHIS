[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^\d{3}$')][string]$BuildNumber,
    [Parameter(Mandatory)][string]$RepositoryRoot,
    [string]$EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
if (-not (Test-Path (Join-Path $repo ".git"))) { throw "Repository root is invalid: $repo" }

$receipt = Join-Path $EvidenceRoot ("Build{0}\completion-receipt.json" -f $BuildNumber)
if (-not (Test-Path $receipt -PathType Leaf)) { throw "Completion receipt is missing; installer archival is blocked: $receipt" }
$receiptData = Get-Content $receipt -Raw | ConvertFrom-Json
if (([string]$receiptData.status).Trim() -ne "verified") { throw "Completion receipt is not verified; installer archival is blocked." }

$archiveRoot = Join-Path $EvidenceRoot ("Build{0}\installer-archive" -f $BuildNumber)
New-Item -ItemType Directory -Path $archiveRoot -Force | Out-Null
$archivePath = Join-Path $archiveRoot ("NRHIS_Sprint2_Build{0}_InstallerArchive.zip" -f $BuildNumber)
$manifestPath = Join-Path $archiveRoot "installer-archive-manifest.json"
$temp = Join-Path ([IO.Path]::GetTempPath()) ("nrhis-installer-archive-{0}-{1}" -f $BuildNumber, [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $temp -Force | Out-Null

try {
    $sources = @(
        (Join-Path $repo ("Build{0}" -f $BuildNumber)),
        (Join-Path $repo ("NRHIS_Sprint2_Build{0}_OneStep.zip" -f $BuildNumber)),
        (Join-Path $repo ("NRHIS_Sprint2_Build{0}_OneStep.zip.sha256" -f $BuildNumber))
    ) | Where-Object { Test-Path $_ }

    if ($sources.Count -eq 0) { throw "No Build$BuildNumber installer artifacts were found to archive." }

    foreach ($source in $sources) {
        Copy-Item $source (Join-Path $temp (Split-Path $source -Leaf)) -Recurse -Force
    }

    if (Test-Path $archivePath) { Remove-Item $archivePath -Force }
    Compress-Archive -Path (Join-Path $temp '*') -DestinationPath $archivePath -CompressionLevel Optimal

    $entries = Get-ChildItem $temp -Recurse -File | ForEach-Object {
        [ordered]@{
            path = $_.FullName.Substring($temp.Length).TrimStart('\','/')
            bytes = $_.Length
            sha256 = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
    [ordered]@{
        schema_version = 1
        build = $BuildNumber
        status = "archived"
        created_utc = [DateTime]::UtcNow.ToString('o')
        archive = $archivePath
        archive_sha256 = (Get-FileHash $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
        files = @($entries)
        policy = "Tracked repository artifacts preserved; only untracked transient extraction remnants may be removed."
    } | ConvertTo-Json -Depth 8 | Set-Content $manifestPath -Encoding utf8
} finally {
    if (Test-Path $temp) { Remove-Item $temp -Recurse -Force -ErrorAction SilentlyContinue }
}

# Remove only known transient paths that are not tracked by Git.
$transientCandidates = @(
    (Join-Path $repo ("Build{0}.previous" -f $BuildNumber))
) + @(Get-ChildItem $repo -Directory -Filter (".nrhis-extract-{0}-*" -f $BuildNumber) -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)

foreach ($candidate in $transientCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique) {
    $relative = $candidate.Substring($repo.Length).TrimStart([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar).Replace('\','/')
    & git -C $repo ls-files --error-unmatch -- $relative 1>$null 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Preserved tracked path: $relative" -ForegroundColor DarkYellow
        continue
    }
    Remove-Item $candidate -Recurse -Force -ErrorAction SilentlyContinue
    if (-not (Test-Path $candidate)) { Write-Host "Removed transient path: $relative" -ForegroundColor DarkGray }
}

Write-Host "Build$BuildNumber installer artifacts archived." -ForegroundColor Green
Write-Host "Archive: $archivePath"
Write-Host "Manifest: $manifestPath"
