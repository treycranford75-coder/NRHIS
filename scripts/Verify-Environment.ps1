[CmdletBinding()]
param(
    [switch]$SkipTests,
    [switch]$SkipRuff
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Assert-Command {
    param([Parameter(Mandatory = $true)][string]$Name)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) { throw "Required command not found: $Name" }
    Write-Host "PASS: $Name available at $($command.Source)" -ForegroundColor Green
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$Description,
        [Parameter(Mandatory = $true)][scriptblock]$Command
    )
    Write-Step $Description
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "$Description failed with exit code $LASTEXITCODE" }
    Write-Host "PASS: $Description" -ForegroundColor Green
}

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $repositoryRoot
try {
    Write-Step "Checking required commands"
    Assert-Command -Name "git"
    Assert-Command -Name "python"

    Invoke-Checked -Description "Checking Python version (>= 3.11)" -Command {
        python -c "import sys; assert sys.version_info >= (3, 11), f'Python 3.11+ required, found {sys.version}'; print(sys.version)"
    }
    Invoke-Checked -Description "Checking Git repository state" -Command {
        git rev-parse --show-toplevel
    }
    Invoke-Checked -Description "Checking NRHIS editable installation" -Command {
        python -c "import nrhis_core, nrhis_harvest; print('NRHIS packages import successfully')"
    }
    Invoke-Checked -Description "Checking runtime dependencies" -Command {
        python -c "import pandas, requests, yaml; print('pandas, requests, and PyYAML import successfully')"
    }
    Invoke-Checked -Description "Checking development dependencies" -Command {
        python -c "import pytest, ruff; print('pytest and ruff import successfully')"
    }

    if (-not $SkipRuff) {
        Invoke-Checked -Description "Running Ruff" -Command { python -m ruff check . }
    } else { Write-Host "SKIP: Ruff check" -ForegroundColor Yellow }

    if (-not $SkipTests) {
        Invoke-Checked -Description "Running pytest" -Command { python -m pytest -q }
    } else { Write-Host "SKIP: pytest" -ForegroundColor Yellow }

    Write-Host "`nNRHIS environment verification completed successfully." -ForegroundColor Green
}
finally { Pop-Location }
