[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string[]]$ExpectedFiles,

    [string[]]$IgnoredPaths = @(
        "Build*/",
        "NRHIS_Sprint2_Build*_OneStep.zip",
        "Start-NRHIS-Build*.ps1"
    )
)

$ErrorActionPreference = "Stop"

function Test-IgnoredPath {
    param(
        [string]$Path,
        [string[]]$Patterns
    )

    foreach ($pattern in $Patterns) {
        if ($Path -like $pattern) {
            return $true
        }
    }

    return $false
}

$expected = @(
    $ExpectedFiles |
        ForEach-Object { $_.Replace("\", "/") } |
        Sort-Object -Unique
)

$staged = @(
    git diff --cached --name-only |
        ForEach-Object { $_.Trim().Replace("\", "/") } |
        Where-Object { $_ } |
        Sort-Object -Unique
)

$unstagedTracked = @(
    git diff --name-only |
        ForEach-Object { $_.Trim().Replace("\", "/") } |
        Where-Object { $_ } |
        Sort-Object -Unique
)

$unexpectedStaged = @($staged | Where-Object { $_ -notin $expected })
$missingStaged = @($expected | Where-Object { $_ -notin $staged })
$unstagedExpected = @($unstagedTracked | Where-Object { $_ -in $expected })

$porcelain = git status --porcelain
$unexpectedUntracked = [System.Collections.Generic.List[string]]::new()

foreach ($line in $porcelain) {
    if ($line.Length -lt 4) {
        continue
    }

    $status = $line.Substring(0, 2)
    $path = $line.Substring(3).Trim().Replace("\", "/")

    if ($status -eq "??" -and -not (Test-IgnoredPath -Path $path -Patterns $IgnoredPaths)) {
        $unexpectedUntracked.Add($path)
    }
}

if ($unexpectedStaged.Count -gt 0) {
    Write-Host "Unexpected staged files:" -ForegroundColor Red
    $unexpectedStaged | ForEach-Object { Write-Host "  $_" }
}

if ($missingStaged.Count -gt 0) {
    Write-Host "Expected files missing from the staged change set:" -ForegroundColor Red
    $missingStaged | ForEach-Object { Write-Host "  $_" }
}

if ($unstagedExpected.Count -gt 0) {
    Write-Host "Expected files still unstaged:" -ForegroundColor Red
    $unstagedExpected | ForEach-Object { Write-Host "  $_" }
}

if ($unexpectedUntracked.Count -gt 0) {
    Write-Host "Unexpected untracked files:" -ForegroundColor Red
    $unexpectedUntracked | ForEach-Object { Write-Host "  $_" }
}

if (
    $unexpectedStaged.Count -gt 0 -or
    $missingStaged.Count -gt 0 -or
    $unstagedExpected.Count -gt 0 -or
    $unexpectedUntracked.Count -gt 0
) {
    throw "Build change-set verification failed."
}

Write-Host ""
Write-Host "Build change-set verification passed." -ForegroundColor Green
Write-Host "Staged file count: $($staged.Count)"
