# Sprint Archive Index Runbook

## List all Sprint archives

```powershell
python -m nrhis_calibration.sprint_archive_index_cli `
  .\reports\sprint-archives
```

## List valid Sprint 2 archives and export JSON

```powershell
python -m nrhis_calibration.sprint_archive_index_cli `
  .\reports\sprint-archives `
  --valid-only `
  --sprint "Sprint 2" `
  --json-output .\reports\sprint2-archive-index.json
```

Invalid archives remain visible unless `--valid-only` is used.
