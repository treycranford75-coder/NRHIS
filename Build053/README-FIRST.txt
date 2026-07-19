NRHIS Sprint 2 Build053

Purpose: Add NOAA/NWS NWPS official forecast and flood-threshold harvesting while retaining USGS as the authoritative source for current observations.

Run from the protected NRHIS repository root:

  .\scripts\release\Start-NrhisBuild.ps1 -BuildNumber "053"

After installation, run the operational forecast harvest with:

  .\scripts\Harvest-NWPS-Forecasts.ps1
