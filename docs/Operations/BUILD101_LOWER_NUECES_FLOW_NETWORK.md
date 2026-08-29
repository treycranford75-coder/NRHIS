# Build101 — Lower Nueces Station-to-Station Flow Network

Build101 begins the main-stem analytical phase of NRHIS using the finalized local USGS archive. It evaluates discharge relationships among:

- 08211000 — Nueces River near Mathis, TX
- 08211200 — Nueces River at Bluntzer, TX
- 08211500 — Nueces River at Calallen, TX

The analysis converts retained instantaneous discharge observations into hourly means, summarizes daily station coverage, and computes descriptive lagged Pearson correlations for Mathis→Bluntzer, Bluntzer→Calallen, and Mathis→Calallen.

A positive lag means the upstream hour at time `t` is compared with the downstream hour at `t + lag`. The best correlation is a statistical alignment only. It is **not** treated as proof of physical travel time or causation. Reservoir operations, diversions, tributary inflows, local gains/losses, backwater, regulation, and missing observations can all affect the relationship.

## Command

```powershell
.\scripts\Analyze-LowerNueces-FlowNetwork.ps1 -StartDate "2017-09-01" -EndDate "2018-06-30"
```

## Outputs

Under `data/nrhis/analysis/lower-nueces-flow-<UTC timestamp>/`:

- `hourly_discharge.csv`
- `daily_station_summary.csv`
- `pair_lag_correlations.csv`
- `pair_best_lags.csv`
- `lower_nueces_flow_network_summary.json`
- `analysis-receipt.json`

The workflow is local-only, makes zero USGS requests, and does not modify the finalized historical archive.
