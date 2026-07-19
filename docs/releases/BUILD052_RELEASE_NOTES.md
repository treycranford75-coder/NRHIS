## NRHIS Sprint 2 — Build052

Build052 adds incremental USGS basin updates and a reporting-readiness data-quality gate.

### Operational command

```powershell
.\scripts\Update-USGS-Incremental.ps1
```

The update resumes from stored history, overlaps recent observations to avoid boundary gaps, deduplicates records, and writes missing, stale, and gap diagnostics.
