# NRHIS Developer Setup

## Purpose

This guide defines the reproducible local development workflow for NRHIS.

## Supported environment

- Windows 10 or Windows 11
- PowerShell 7 preferred; Windows PowerShell is supported
- Git
- Python 3.11 or later

The authoritative Python requirement is declared in `pyproject.toml`.

## Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Install NRHIS and development dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Verify the environment

```powershell
.\scripts\Verify-Environment.ps1
```

Optional fast checks:

```powershell
.\scripts\Verify-Environment.ps1 -SkipTests
.\scripts\Verify-Environment.ps1 -SkipRuff
```

## Standard validation commands

```powershell
python -m pytest -q
python -m ruff check .
git diff --check
git diff --cached --check
```

## USGS harvest smoke test

```powershell
.\scripts\Harvest-USGS.ps1 -StartDate 2026-07-17 -EndDate 2026-07-17
```

## Branch workflow

```powershell
git switch develop
git pull origin develop
git switch -c feature/<work-name>
git push -u origin feature/<work-name>
```

## Legacy calibration preservation

Do not modify, remove, rename, or refactor files under `src/nrhis_calibration/legacy`.

## Troubleshooting

### `ModuleNotFoundError`

```powershell
python -m pip install -e ".[dev]"
```

### PowerShell script execution is blocked

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### OneDrive locks Git directories

Close File Explorer windows and editors using the repository, then retry.
