[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [switch]$RequireGitHubAuthentication
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo

$problems = [System.Collections.Generic.List[string]]::new()

function Test-PowerShellFile {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path $Path -PathType Leaf)) {
        $problems.Add("Missing required script: $Path")
        return
    }

    $tokens = $null
    $errors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile(
        (Resolve-Path $Path),
        [ref]$tokens,
        [ref]$errors
    )

    foreach ($parseError in @($errors)) {
        $problems.Add("PowerShell syntax error in ${Path}: $($parseError.Message)")
    }
}

$requiredScripts = @(
    'scripts/release/Start-NrhisBuild.ps1',
    'scripts/release/New-NrhisPullRequest.ps1',
    'scripts/release/Finish-NrhisBuildLifecycle.ps1',
    'scripts/release/Resume-NrhisBuildLifecycle.ps1',
    'scripts/release/Complete-NrhisBuild.ps1',
    'scripts/release/Archive-NrhisInstallerArtifacts.ps1'
)

foreach ($relativePath in $requiredScripts) {
    Test-PowerShellFile -Path (Join-Path $repo $relativePath)
}

$finishPath = Join-Path $repo 'scripts/release/Finish-NrhisBuildLifecycle.ps1'
if (Test-Path $finishPath -PathType Leaf) {
    $finishText = Get-Content $finishPath -Raw
    $requiredFinishContracts = @(
        'gh pr checks',
        '--watch',
        'gh pr merge',
        'Complete-Build$BuildNumber.ps1',
        'Archive-NrhisInstallerArtifacts.ps1',
        "status -ne 'verified'",
        'verified -ne $true',
        'Local feature branch already absent:',
        'Remote feature branch already absent:'
    )
    foreach ($contract in $requiredFinishContracts) {
        if (-not $finishText.Contains($contract)) {
            $problems.Add("Finish lifecycle contract missing: $contract")
        }
    }
}

$completePath = Join-Path $repo 'scripts/release/Complete-NrhisBuild.ps1'
if (Test-Path $completePath -PathType Leaf) {
    $completeText = Get-Content $completePath -Raw
    foreach ($contract in @("status = 'verified'", 'verified = $true', 'gh release view', 'gh release create')) {
        if (-not $completeText.Contains($contract)) {
            $problems.Add("Completion helper contract missing: $contract")
        }
    }
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    $problems.Add('Git is not available on PATH.')
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    $problems.Add('GitHub CLI (gh) is not available on PATH.')
}
elseif ($RequireGitHubAuthentication) {
    & gh auth status 1>$null 2>$null
    if ($LASTEXITCODE -ne 0) {
        $problems.Add('GitHub CLI is not authenticated.')
    }
}

$result = [ordered]@{
    schema_version = 1
    checked_at = [DateTime]::UtcNow.ToString('o')
    repository_root = $repo
    healthy = ($problems.Count -eq 0)
    problem_count = $problems.Count
    problems = @($problems)
}

$resultPath = Join-Path $repo 'data/nrhis/release/lifecycle-preflight.json'
New-Item -ItemType Directory -Path (Split-Path $resultPath -Parent) -Force | Out-Null
$json = $result | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($resultPath, $json + "`n", [System.Text.UTF8Encoding]::new($false))

if ($problems.Count -gt 0) {
    Write-Host 'NRHIS release lifecycle preflight failed:' -ForegroundColor Red
    foreach ($problem in $problems) {
        Write-Host " - $problem" -ForegroundColor Red
    }
    throw "Release lifecycle preflight found $($problems.Count) problem(s)."
}

Write-Host 'NRHIS release lifecycle preflight passed.' -ForegroundColor Green
Write-Host "Receipt: $resultPath" -ForegroundColor DarkGray
return $result
