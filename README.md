# Nueces River Hydrologic Intelligence System (NRHIS)

NRHIS is a version-controlled hydrologic intelligence platform for the Nueces River Basin.

## Version

0.1.0-foundation

## Initial Objectives

1. Preserve source data and legacy calibration work.
2. Build configuration-driven data harvesting.
3. Maintain traceable QA, event, GIS, and publication workflows.
4. Reproduce every published product from archived data.

## Quick Start on Windows

Open PowerShell in the repository root and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\Initialize-NRHIS.ps1
```

To copy the existing Upper Nueces Pass 1 package into the protected legacy area:

```powershell
.\scripts\Migrate-Legacy-Pass1.ps1
```

The migration script copies files. It does not delete or modify the original package.

## Repository Layout

- `config/` controlled station, reach, reservoir, model, and publication registries
- `src/` Python source modules
- `data/raw/` immutable source retrievals; excluded from Git by default
- `data/processed/` standardized outputs; excluded from Git by default
- `events/` event workspaces
- `gis/` GIS-ready products
- `reports/` generated reports
- `archive/` frozen release and publication records
- `docs/` architecture, standards, operations, publications, and research documentation
