NRHIS Sprint 2 Build051

Purpose: add restart-safe historical USGS backfill for the Nueces-Frio basin.

From the NRHIS repository root run:
  .\scripts\release\Start-NrhisBuild.ps1 -BuildNumber "051"

After installation, run historical extraction with:
  .\scripts\Backfill-USGS-History.ps1

Default range: 2024-02-01 through today. Default chunk size: 7 days.
