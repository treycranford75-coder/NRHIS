[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$BuildNumber,
    [Parameter(Mandatory)][string]$RepositoryRoot,
    [string]$EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
if (-not (Test-Path (Join-Path $repo ".git"))) { throw "CI parity gate requires the NRHIS repository root." }
Set-Location $repo

$evidenceDir = Join-Path $EvidenceRoot ("Build{0}\pre-push-ci" -f $BuildNumber)
New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null
$stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
$logPath = Join-Path $evidenceDir ("ci-parity-{0}.log" -f $stamp)
$receiptPath = Join-Path $evidenceDir "ci-parity-receipt.json"

$steps = New-Object System.Collections.Generic.List[object]

function Invoke-ParityStep {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][scriptblock]$Command
    )
    $started = [DateTime]::UtcNow
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & $Command 2>&1
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previous
    }
    if ($null -eq $exitCode) { $exitCode = 0 }
    $ended = [DateTime]::UtcNow
    @("===== $Name =====") + @($output | ForEach-Object { [string]$_ }) | Add-Content -Path $logPath -Encoding utf8
    $steps.Add([ordered]@{
        name = $Name
        exit_code = [int]$exitCode
        started_utc = $started.ToString('o')
        ended_utc = $ended.ToString('o')
        duration_seconds = [math]::Round(($ended - $started).TotalSeconds, 3)
    })
    if ($exitCode -ne 0) { throw "CI parity step failed: $Name (exit code $exitCode). See $logPath" }
}

if (Get-Command ruff -ErrorAction SilentlyContinue) {
    Invoke-ParityStep -Name "ruff check ." -Command { ruff check . }
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw "Python is required for the CI parity gate." }

Invoke-ParityStep -Name "python compileall" -Command { python -m compileall -q src tests }
Invoke-ParityStep -Name "pytest branch coverage" -Command {
    python -m pytest --cov=src --cov-branch --cov-report=xml --cov-fail-under=80 -q
}
Invoke-ParityStep -Name "git diff --check" -Command { git diff --check }

[ordered]@{
    schema_version = 1
    build = $BuildNumber
    status = "passed"
    repository_root = $repo
    commit = ((git rev-parse HEAD) | Out-String).Trim()
    generated_utc = [DateTime]::UtcNow.ToString('o')
    log = $logPath
    steps = $steps
} | ConvertTo-Json -Depth 8 | Set-Content -Path $receiptPath -Encoding utf8

Write-Host "CI parity gate passed." -ForegroundColor Green
Write-Host "CI parity receipt: $receiptPath" -ForegroundColor Green
