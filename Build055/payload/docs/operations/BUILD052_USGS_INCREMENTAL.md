# Build052 — Incremental USGS Update and Data-Quality Gate

Build052 turns the historical backfill into a repeatable operational update.

## Command

```powershell
.\scripts\Update-USGS-Incremental.ps1
```

The command resumes from the newest stored observation with a two-day overlap, performs duplicate-safe retrieval, and writes:

- `data/nrhis/historical/usgs_observations_history.jsonl`
- `data/nrhis/historical/usgs_observations_history.csv`
- `data/nrhis/quality/usgs_data_quality_summary.json`
- `data/nrhis/quality/usgs_parameter_status.csv`
- `data/nrhis/quality/usgs_detected_gaps.csv`
- `data/nrhis/receipts/usgs_incremental_update_receipt.json`

`ready_for_reporting` is false whenever a configured station/parameter is missing or stale. Gap detection is informational and does not alter source observations.
