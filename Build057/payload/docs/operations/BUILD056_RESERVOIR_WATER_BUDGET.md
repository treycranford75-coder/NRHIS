# Build056 Reservoir Evaporation and Water Budget

Build056 calculates daily evaporation and a 24-hour water budget separately for Choke Canyon Reservoir and Lake Corpus Christi.

Daily evaporation data are used when supplied in `data/nrhis/meteorology/reservoir_evaporation_daily.json`. Otherwise the output is explicitly labeled as a monthly-climatology estimate. Surface area comes from the latest TWDB reservoir harvest.

Outputs include acre-feet/day, million gallons/day, rolling 7-day and month-to-date evaporation, inflow, municipal diversions, environmental releases, other outflow, calculated net storage change, observed storage change, and residual. Missing flux terms cause `budget_complete=false` rather than fabricated values.

Run:

```powershell
.\scripts\Build-Reservoir-Water-Budget.ps1
```
