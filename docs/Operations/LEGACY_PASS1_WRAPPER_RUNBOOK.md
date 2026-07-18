# Legacy Pass1 Wrapper Runbook

## Preflight

```powershell
git status
.\scripts\Verify-Environment.ps1
python -m pytest -q .\tests\test_legacy_preservation.py
```

## Dry run

```powershell
.\scripts\Invoke-LegacyPass1.ps1 -DryRun
```

## Controlled execution

```powershell
.\scripts\Invoke-LegacyPass1.ps1 -OutputRoot .\reports\legacy-pass1 -TimeoutSeconds 600
```

## Post-run integrity check

```powershell
python -m pytest -q .\tests\test_legacy_preservation.py
git status --short
```
