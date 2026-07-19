# Calibration Reference Approval Runbook

## Validate before approval

```powershell
python -m nrhis_calibration.reference_cli `
  .\data\calibration-reference-cases\<CASE_ID>\case.json
```

## Approve

```powershell
python -m nrhis_calibration.reference_approval_cli approve `
  .\data\calibration-reference-cases\<CASE_ID>\case.json `
  --reviewer "Reviewer Name" `
  --rationale "Artifacts, provenance, units, and tolerances reviewed."
```

## Confirm approved validation

```powershell
python -m nrhis_calibration.reference_cli `
  .\data\calibration-reference-cases\<CASE_ID>\case.json `
  --require-approved
```

## Revoke

```powershell
python -m nrhis_calibration.reference_approval_cli revoke `
  .\data\calibration-reference-cases\<CASE_ID>\case.json `
  --reviewer "Reviewer Name" `
  --rationale "Superseded, corrected, or withdrawn."
```

Never edit approval or revocation records manually.
