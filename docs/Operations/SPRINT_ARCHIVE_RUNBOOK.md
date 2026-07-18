# Sprint Archive Runbook

```powershell
python -m nrhis_calibration.sprint_archive_cli create `
  .\reports\sprint-archives `
  sprint2-closeout `
  .\reports\sprint2-release-inventory.json `
  .\reports\sprint2-closeout.json `
  --metadata-json '{"sprint":"Sprint 2","status":"accepted"}'
```

```powershell
python -m nrhis_calibration.sprint_archive_cli validate `
  .\reports\sprint-archives\sprint2-closeout\sprint_archive_manifest.json
```
