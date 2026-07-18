# USGS Harvest Engine Runbook

## Purpose

`Harvest-USGS.ps1` retrieves USGS NWIS instantaneous observations using an approved YAML
station registry. Each run preserves the source JSON, emits a normalized CSV, records SHA-256
hashes and request metadata, and writes an operational log.

## Standard run

```powershell
.\scripts\Harvest-USGS.ps1
```

The default run uses `config/stations/lower_nueces.yml` and requests the current day plus the
prior day. A controlled historical window can be supplied:

```powershell
.\scripts\Harvest-USGS.ps1 -StartDate 2026-07-01 -EndDate 2026-07-17
```

## Outputs

- `data/raw/usgs/<run-id>/nwis_iv.json`: immutable source response
- `data/processed/usgs/<run-id>/observations.csv`: normalized observations
- `data/processed/usgs/<run-id>/metadata.json`: provenance, counts, and SHA-256 hashes
- `reports/logs/harvest-usgs-<timestamp>.log`: execution log

Generated data are excluded from Git. For publication use, freeze the applicable run under a
controlled snapshot or archive process rather than editing source artifacts.

## Failure behavior

The command exits nonzero when registry validation, network retrieval, response decoding, or
artifact writing fails. A failed run must not be represented as a completed harvest.
