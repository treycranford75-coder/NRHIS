# Calibration Reference Capture Runbook

## 1. Produce a successful wrapper run

```powershell
.\scripts\Invoke-LegacyPass1.ps1 -DryRun
```

For production reference work, use an approved controlled execution rather than
a dry run.

## 2. Capture the run

```powershell
python -m nrhis_calibration.reference_capture_cli `
  .\reports\legacy-pass1\<RUN_ID> `
  .\data\calibration-reference-cases `
  legacy-pass1-<CASE_ID> `
  --description "Controlled legacy Pass1 reference capture"
```

## 3. Validate the generated manifest

```powershell
python -m nrhis_calibration.reference_cli `
  .\data\calibration-reference-cases\legacy-pass1-<CASE_ID>\case.json
```

Do not use `--require-approved` until the case has completed a separate approval
workflow.

## 4. Review

Confirm:

- source run succeeded;
- artifact paths are correct;
- SHA-256 values validate;
- case remains unapproved;
- no legacy file changed.
