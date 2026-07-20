[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$BuildNumber,
    [Parameter(Mandatory)][string]$RepositoryRoot,
    [string]$EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
if (-not (Test-Path (Join-Path $repo ".git"))) { throw "Workflow contract gate requires the NRHIS repository root." }
Set-Location $repo

$starter = Join-Path $repo "scripts\release\Start-NrhisBuild.ps1"
if (-not (Test-Path $starter -PathType Leaf)) { throw "Permanent build starter is missing: $starter" }

$text = Get-Content $starter -Raw
$requiredPatterns = [ordered]@{
    package_name = 'NRHIS_Sprint2_Build\$\{BuildNumber\}_OneStep\.zip'
    downloads_search = 'Join-Path\s+\$HOME\s+"Downloads"'
    archive_extraction = 'Expand-Archive'
    repository_guard = 'Test-Path\s+\(Join-Path\s+\$repo\s+"\.git"\)'
    apply_script_path = 'Apply-Build.*BuildNumber.*\.ps1'
    apply_invocation = '&\s+\$entry\s+@params'
    checksum_validation = 'Get-FileHash\s+\$zip\s+-Algorithm\s+SHA256'
    extraction_reuse = '\$reuse'
}

$missing = New-Object System.Collections.Generic.List[string]
foreach ($item in $requiredPatterns.GetEnumerator()) {
    if (-not [regex]::IsMatch($text, $item.Value)) { $missing.Add($item.Key) }
}
if ($missing.Count -gt 0) { throw "Workflow starter contract failed. Missing: $($missing -join ', ')" }

$evidenceDir = Join-Path $EvidenceRoot ("Build{0}\pre-push-contract" -f $BuildNumber)
New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null
$stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
$logPath = Join-Path $evidenceDir ("workflow-contract-{0}.log" -f $stamp)
$receiptPath = Join-Path $evidenceDir "workflow-contract-receipt.json"

$targetTests = @(
    "tests/test_release_workflow_build026.py",
    "tests/test_release_workflow_build032.py"
) | Where-Object { Test-Path (Join-Path $repo $_) }
if ($targetTests.Count -eq 0) { throw "No workflow contract tests were found." }

$previous = $ErrorActionPreference
$ErrorActionPreference = "Continue"
try {
    $output = & python -m pytest @targetTests -q 2>&1
    $exitCode = $LASTEXITCODE
} finally {
    $ErrorActionPreference = $previous
}
@($output | ForEach-Object { [string]$_ }) | Set-Content -Path $logPath -Encoding utf8
if ($exitCode -ne 0) { throw "Workflow contract tests failed (exit code $exitCode). See $logPath" }

[ordered]@{
    schema_version = 1
    build = $BuildNumber
    status = "passed"
    repository_root = $repo
    generated_utc = [DateTime]::UtcNow.ToString('o')
    starter = $starter
    required_contracts = @($requiredPatterns.Keys)
    tests = $targetTests
    log = $logPath
} | ConvertTo-Json -Depth 6 | Set-Content -Path $receiptPath -Encoding utf8

Write-Host "Workflow contract preflight passed." -ForegroundColor Green
Write-Host "Workflow contract receipt: $receiptPath" -ForegroundColor Green
