NRHIS Sprint 2 Build052

Purpose: add restart-safe incremental USGS updates and a basin data-quality gate.

From the NRHIS repository root run:
  .\scripts\release\Start-NrhisBuild.ps1 -BuildNumber "052"

After installation, run:
  .\scripts\Update-USGS-Incremental.ps1

The updater resumes from stored history with a two-day overlap and writes missing, stale, and gap diagnostics for reporting readiness.
