# Build059 — SALT03 Coastal Water-Quality Harvest

Build059 retrieves fixed-station observations from the official Water Data for Texas Coastal API for SALT03 in Nueces Bay.

## Command

```powershell
.\scripts\Harvest-SALT03-Coastal.ps1
```

## Outputs

- `data/nrhis/coastal/salt03_current_conditions.json`
- `data/nrhis/coastal/salt03_current_conditions.csv`
- `data/nrhis/coastal/salt03_parameter_status.csv`
- `data/nrhis/coastal/salt03_observations.jsonl`
- `data/nrhis/coastal/salt03_readiness.json`
- `data/nrhis/receipts/salt03_coastal_harvest_receipt.json`

The harvester discovers available parameters from the station metadata endpoint, retrieves preferred parameters when available, archives raw responses with SHA-256 evidence, and fails reporting readiness when required salinity data are missing or stale.
