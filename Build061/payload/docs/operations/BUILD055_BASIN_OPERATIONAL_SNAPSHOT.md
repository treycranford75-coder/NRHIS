# Build055 — Integrated Basin Operational Snapshot

Build055 combines current USGS observations, USGS quality status, and NOAA/NWS NWPS forecasts into one reporting-ready station table.

## Run

```powershell
.\scripts\Build-Basin-Operational-Snapshot.ps1 -RefreshSources
```

## Outputs

- `data/nrhis/operational/basin_operational_snapshot.json`
- `data/nrhis/operational/basin_operational_snapshot.csv`
- `data/nrhis/operational/basin_operational_alerts.csv`
- `data/nrhis/operational/basin_reporting_readiness.json`
- `data/nrhis/receipts/basin_operational_snapshot_receipt.json`

USGS remains authoritative for current observations. NWPS supplies forecasts and official flood thresholds. Estimated TDS is clearly labeled and uses specific conductance multiplied by 0.65.
