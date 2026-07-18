# Legacy Pass1 Compatibility Wrapper — Sprint 2 Build005

## Purpose

Build005 introduces an additive compatibility layer for the preserved legacy Pass1 calibration implementation.

The wrapper launches the preserved script as a separate process and captures a structured execution record. It does not refactor, import, or modify the legacy source.

## Components

- `src/nrhis_calibration/compat.py`
- `scripts/Invoke-LegacyPass1.ps1`
- `tests/test_calibration_compat.py`

## Isolation boundary

The wrapper validates the preserved script, executes it through a subprocess boundary, captures stdout and stderr, records timing and return code, records the legacy script SHA-256, and writes metadata outside the legacy tree.

## Dry run

```powershell
.\scripts\Invoke-LegacyPass1.ps1 -DryRun
```

## Controlled execution

```powershell
.\scripts\Invoke-LegacyPass1.ps1 -OutputRoot .\reports\legacy-pass1 -TimeoutSeconds 600
```

## Output contract

Each run creates a UTC directory containing `stdout.log`, `stderr.log`, and `metadata.json`.

## Preservation requirement

All pre-existing files under `src/nrhis_calibration/legacy` remain governed by the Build002 SHA-256 preservation baseline.
