[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$BuildNumber,
    [Parameter(Mandatory)][string]$Repository,
    [Parameter(Mandatory)][string]$Tag,
    [Parameter(Mandatory)][string]$ReleaseTitle,
    [Parameter(Mandatory)][string]$NotesFile,
    [string]$EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence"),
    [string]$ReleaseAsset,
    [switch]$BrowserOnly
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-GitHubJson {
    param([Parameter(Mandatory)][string]$Uri)
    $headers = @{
        "Accept" = "application/vnd.github+json"
        "User-Agent" = "NRHIS-Build$BuildNumber"
        "X-GitHub-Api-Version" = "2022-11-28"
    }
    return Invoke-RestMethod -Uri $Uri -Headers $headers
}

function Resolve-GitHubTagCommit {
    param([Parameter(Mandatory)][string]$Repo, [Parameter(Mandatory)][string]$ReleaseTag)
    $encodedTag = [uri]::EscapeDataString($ReleaseTag)
    $ref = Invoke-GitHubJson -Uri "https://api.github.com/repos/$Repo/git/ref/tags/$encodedTag"
    $sha = ([string]$ref.object.sha).Trim()
    $type = ([string]$ref.object.type).Trim()
    if ($type -eq "tag") {
        $tagObject = Invoke-GitHubJson -Uri "https://api.github.com/repos/$Repo/git/tags/$sha"
        $sha = ([string]$tagObject.object.sha).Trim()
        $type = ([string]$tagObject.object.type).Trim()
    }
    if ($type -ne "commit" -or -not $sha) { throw "Tag '$ReleaseTag' did not resolve to a commit." }
    return $sha
}

function Test-GhAuthentication {
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { return $false }
    gh auth status --hostname github.com *> $null
    return ($LASTEXITCODE -eq 0)
}

$repoRoot = (Get-Location).Path
if (-not (Test-Path (Join-Path $repoRoot ".git"))) { throw "Run from the NRHIS repository root." }
if ((git branch --show-current).Trim() -ne "develop") { throw "Automated release completion requires the develop branch." }
if (-not (Test-Path $NotesFile)) { throw "Release notes file not found: $NotesFile" }

Write-Host "Synchronizing develop without pruning..." -ForegroundColor Cyan
git fetch origin --no-prune --tags
if ($LASTEXITCODE -ne 0) { throw "Git fetch failed." }
git pull --ff-only --no-prune origin develop
if ($LASTEXITCODE -ne 0) { throw "Git pull failed." }

$expectedCommit = (git rev-parse HEAD).Trim()
$remoteCommit = (git rev-parse origin/develop).Trim()
if ($expectedCommit -ne $remoteCommit) { throw "Local develop does not match origin/develop." }

$buildFolder = Join-Path $EvidenceRoot ("Build{0}" -f $BuildNumber)
New-Item -ItemType Directory -Path $buildFolder -Force | Out-Null
$handoffPath = Join-Path $buildFolder "publication-handoff.json"
$handoff = [ordered]@{
    schema_version = 3
    build = $BuildNumber
    repository = $Repository
    tag = $Tag
    expected_merged_commit = $expectedCommit
    release_title = $ReleaseTitle
    prerelease = $true
    latest = $false
    notes_file = $NotesFile
    release_asset = $ReleaseAsset
    generated_utc = [DateTime]::UtcNow.ToString("o")
}
$handoff | ConvertTo-Json -Depth 8 | Set-Content $handoffPath -Encoding utf8

$encodedTag = [uri]::EscapeDataString($Tag)
$releaseUri = "https://api.github.com/repos/$Repository/releases/tags/$encodedTag"
$release = $null
try { $release = Invoke-GitHubJson -Uri $releaseUri } catch { $release = $null }

if ($null -eq $release) {
    $canUseGh = (-not $BrowserOnly) -and (Test-GhAuthentication)
    if ($canUseGh) {
        Write-Host "Publishing GitHub pre-release automatically..." -ForegroundColor Cyan
        $arguments = @(
            "release", "create", $Tag,
            "--repo", $Repository,
            "--target", $expectedCommit,
            "--title", $ReleaseTitle,
            "--notes-file", $NotesFile,
            "--prerelease"
        )
        if ($ReleaseAsset) {
            $resolvedAsset = (Resolve-Path $ReleaseAsset).Path
            $arguments += $resolvedAsset
        }
        & gh @arguments
        if ($LASTEXITCODE -ne 0) { throw "GitHub CLI release publication failed." }
    } else {
        $newReleaseUrl = "https://github.com/$Repository/releases/new?tag=$encodedTag&target=$expectedCommit"
        Set-Clipboard -Value $newReleaseUrl -ErrorAction SilentlyContinue
        try { Start-Process $newReleaseUrl } catch { }
        Write-Host "Browser publication required." -ForegroundColor Yellow
        Write-Host "Publish tag $Tag at commit $expectedCommit as a pre-release, not latest."
        Write-Host "Handoff: $handoffPath"
        Write-Host "Rerun the same Build$BuildNumber command after publication."
        return
    }
    $release = Invoke-GitHubJson -Uri $releaseUri
}

$actualTag = ([string]$release.tag_name).Trim()
if ($actualTag -ne $Tag) { throw "Published release tag mismatch. Expected '$Tag'; found '$actualTag'." }
if ([bool]$release.draft) { throw "Published release remains a draft." }
if (-not [bool]$release.prerelease) { throw "Published release is not marked as a pre-release." }

$resolvedCommit = (Resolve-GitHubTagCommit -Repo $Repository -ReleaseTag $Tag).Trim()
if ($resolvedCommit -ne $expectedCommit) { throw "Release tag commit mismatch. Expected '$expectedCommit'; found '$resolvedCommit'." }

$evidence = [ordered]@{
    schema_version = 3
    build = $BuildNumber
    repository = $Repository
    tag_name = $actualTag
    name = [string]$release.name
    html_url = [string]$release.html_url
    release_id = [string]$release.id
    target_commitish_original = [string]$release.target_commitish
    target_commitish = $resolvedCommit
    published_commit = $resolvedCommit
    prerelease = [bool]$release.prerelease
    draft = [bool]$release.draft
    published_at = [string]$release.published_at
    verified_utc = [DateTime]::UtcNow.ToString("o")
}
$evidencePath = Join-Path $buildFolder "public-release-verification.json"
$evidence | ConvertTo-Json -Depth 10 | Set-Content $evidencePath -Encoding utf8

$closure = Join-Path $PSScriptRoot "Close-NrhisReleaseVerification.ps1"
if (-not (Test-Path $closure)) { throw "Verification closure helper not found: $closure" }
& $closure -BuildNumber $BuildNumber -Tag $Tag -ExpectedCommit $expectedCommit -EvidenceJson $evidencePath -EvidenceRoot $EvidenceRoot

$receiptPath = Join-Path $buildFolder "completion-receipt.json"
if (-not (Test-Path $receiptPath)) { throw "Completion receipt was not created." }
$receipt = Get-Content $receiptPath -Raw | ConvertFrom-Json
if (([string]$receipt.build).Trim() -ne $BuildNumber) { throw "Completion receipt build mismatch." }
if (([string]$receipt.tag).Trim() -ne $Tag) { throw "Completion receipt tag mismatch." }
$verifiedCommit = ([string]$receipt.verified_commit).Trim()
if (-not $expectedCommit.StartsWith($verifiedCommit, [StringComparison]::OrdinalIgnoreCase) -and
    -not $verifiedCommit.StartsWith($expectedCommit, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Completion receipt commit mismatch."
}

Write-Host "Build$BuildNumber automated publication and verification completed." -ForegroundColor Green
Write-Host "Release: $($release.html_url)"
Write-Host "Receipt: $receiptPath"
