# Build055 — TWDB Reservoir Operations Harvest

Build055 introduces a production harvester for Choke Canyon Reservoir and Lake Corpus Christi.

Operational command:

```powershell
.\scripts\Harvest-TWDB-Reservoirs.ps1
```

Primary products:

- `data\nrhis\reservoirs\reservoir_current_conditions.json`
- `data\nrhis\reservoirs\reservoir_current_conditions.csv`
- `data\nrhis\reservoirs\reservoir_combined_summary.json`
- `data\nrhis\reservoirs\reservoir_observations.jsonl`
- `data\nrhis\receipts\twdb_reservoir_harvest_receipt.json`
