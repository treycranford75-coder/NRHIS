[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$BuildNumber,
    [Parameter(Mandatory)][string]$Tag,
    [Parameter(Mandatory)][string]$ExpectedCommit,
    [Parameter(Mandatory)][string]$EvidenceJson,
    [string]$EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Get-FirstValue {
    param([object]$Object, [string[]]$Names)
    foreach ($name in $Names) {
        $property = $Object.PSObject.Properties[$name]
        if ($null -ne $property -and $null -ne $property.Value -and [string]$property.Value -ne "") {
            return [string]$property.Value
        }
    }
    return $null
}

$sourcePath = (Resolve-Path $EvidenceJson).Path
$evidence = Get-Content $sourcePath -Raw | ConvertFrom-Json

$actualTag = Get-FirstValue $evidence @("tag_name", "tag", "release_tag", "expected_tag")
$actualCommit = Get-FirstValue $evidence @("target_commitish", "commit", "commit_sha", "published_commit", "expected_commit")
$prerelease = $evidence.PSObject.Properties["prerelease"]
$draft = $evidence.PSObject.Properties["draft"]

if ($actualTag -ne $Tag) {
    throw "Verification evidence tag mismatch. Expected '$Tag'; found '$actualTag'."
}
if (-not $actualCommit) {
    throw "Verification evidence does not contain a commit value."
}
if (-not $ExpectedCommit.StartsWith($actualCommit, [System.StringComparison]::OrdinalIgnoreCase) -and
    -not $actualCommit.StartsWith($ExpectedCommit, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Verification evidence commit mismatch. Expected '$ExpectedCommit'; found '$actualCommit'."
}
if ($null -ne $prerelease -and -not [bool]$prerelease.Value) {
    throw "Published release is not marked as a pre-release."
}
if ($null -ne $draft -and [bool]$draft.Value) {
    throw "Published release remains a draft."
}

$buildFolder = Join-Path $EvidenceRoot ("Build{0}" -f $BuildNumber)
New-Item -ItemType Directory -Path $buildFolder -Force | Out-Null
$destination = Join-Path $buildFolder ("release-verification-{0}.json" -f $Tag.Replace("/", "_"))
Copy-Item $sourcePath $destination -Force

$receipt = [ordered]@{
    build = $BuildNumber
    tag = $Tag
    expected_commit = $ExpectedCommit
    verified_commit = $actualCommit
    prerelease = if ($null -ne $prerelease) { [bool]$prerelease.Value } else { $null }
    draft = if ($null -ne $draft) { [bool]$draft.Value } else { $null }
    evidence_file = $destination
    verified_utc = [DateTime]::UtcNow.ToString("o")
    status = "verified"
}
$receiptPath = Join-Path $buildFolder "completion-receipt.json"
$receipt | ConvertTo-Json -Depth 6 | Set-Content $receiptPath -Encoding utf8

& (Join-Path $PSScriptRoot "Write-NrhisReleaseEvidenceIndex.ps1") -EvidenceRoot $EvidenceRoot
Write-Host "Build$BuildNumber release verification closed." -ForegroundColor Green
Write-Host "Receipt: $receiptPath"
