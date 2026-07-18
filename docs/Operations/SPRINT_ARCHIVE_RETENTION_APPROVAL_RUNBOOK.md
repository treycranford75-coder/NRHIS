# Sprint Archive Retention Approval Runbook

```powershell
python -m nrhis_calibration.archive_retention_approval_cli approve `
  .\reports\sprint-archive-retention.json `
  .\reports\sprint-archive-retention-approval.json `
  --reviewer "Trey Cranford" `
  --rationale "Reviewed for Sprint 2 closeout."
```

Validate with:

```powershell
python -m nrhis_calibration.archive_retention_approval_cli validate `
  .\reports\sprint-archive-retention.json `
  .\reports\sprint-archive-retention-approval.json
```
