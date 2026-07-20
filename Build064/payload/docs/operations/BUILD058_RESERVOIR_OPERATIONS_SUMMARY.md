# Build058 Reservoir Operations Summary

Build058 assembles the current TWDB reservoir conditions, reservoir evaporation and 24-hour water budget, and estimated reservoir response into one reporting-ready product for Choke Canyon Reservoir and Lake Corpus Christi.

## Run

```powershell
.\scripts\Build-Reservoir-Operations-Summary.ps1
```

## Outputs

- `data/nrhis/reservoirs/reservoir_operations_summary.json`
- `data/nrhis/reservoirs/reservoir_operations_summary.csv`
- `data/nrhis/reservoirs/reservoir_operations_readiness.json`
- `data/nrhis/receipts/reservoir_operations_summary_receipt.json`

The readiness result is `ready`, `conditional`, or `not_ready`. Missing or stale source data are never silently replaced with invented values.
