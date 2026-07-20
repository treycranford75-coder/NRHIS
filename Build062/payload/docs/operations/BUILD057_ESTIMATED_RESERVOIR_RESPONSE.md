# Build057 Estimated Reservoir Response

Build057 estimates event-response ranges for Choke Canyon Reservoir and Lake Corpus Christi using the latest NWPS peak-flow forecasts, configured routing windows, current TWDB storage, and low/central/high capture factors.

Run:

```powershell
.\scripts\Estimate-Reservoir-Response.ps1
```

Outputs:
- `data/nrhis/reservoirs/reservoir_response_estimate.json`
- `data/nrhis/reservoirs/reservoir_response_estimate.csv`
- `data/nrhis/receipts/reservoir_response_estimate_receipt.json`

Every row includes current storage, estimated event gain, projected post-event storage and percent full, confidence, basis, and the required changing-data caveat.
