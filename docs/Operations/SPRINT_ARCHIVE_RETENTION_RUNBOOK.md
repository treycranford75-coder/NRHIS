# Sprint Archive Retention Runbook

```powershell
python -m nrhis_calibration.archive_retention_cli `
  .\reports\sprint-archives `
  --retain-latest 3 `
  --json-output .\reports\sprint-archive-retention.json
```

The plan is non-destructive. Review every `review` and `quarantine` decision
before any separate operational action is approved.
