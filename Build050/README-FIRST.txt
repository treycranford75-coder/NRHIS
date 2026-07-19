NRHIS Sprint 2 Build050 - Production USGS Basin Harvest

Run from the protected NRHIS repository root:

  .\scripts\release\Start-NrhisBuild.ps1 -BuildNumber "050"

Build050 delivers live USGS Instantaneous Values extraction, raw response archival, normalized and duplicate-safe observation storage, stale/provisional/missing validation, and current-condition JSON/CSV outputs for the Nueces–Frio basin station set.

After installation, the operational harvest command is:

  .\scripts\Harvest-USGS-Production.ps1
