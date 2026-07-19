# Build053 NOAA/NWS NWPS Forecast Harvest

Build053 adds official NWS forecast and flood-threshold retrieval through the NOAA National Water Prediction Service API.

## Source policy

USGS Instantaneous Values remains the authoritative source for current observed discharge, stage, and water-quality readings. NWPS is used for official NWS forecasts, flood categories, and threshold metadata.

## Command

```powershell
.\scripts\Harvest-NWPS-Forecasts.ps1
```

## Outputs

- `data/nrhis/nwps/nwps_forecasts.json`
- `data/nrhis/nwps/nwps_forecasts.csv`
- `data/nrhis/nwps/nwps_flood_thresholds.csv`
- `data/nrhis/nwps/nwps_station_status.csv`
- `data/nrhis/nwps/nwps_readiness.json`
- `data/nrhis/receipts/nwps_forecast_harvest_receipt.json`
- raw NOAA responses under `data/nrhis/raw/nwps/<timestamp>/`

The station-status product distinguishes endpoint success from forecast availability because not every configured gauge necessarily receives an official NWS forecast at all times.
