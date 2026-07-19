# Payload Consistency and Complete Staging Runbook

Validate payload consistency:

```powershell
.\scripts\release\Test-NrhisPayloadConsistency.ps1 `
  -PayloadRoot ".\Build033\payload"
```

Stage and verify the complete Build033 change set:

```powershell
.\scripts\release\Stage-NrhisBuildPayload.ps1 `
  -PayloadRoot ".\Build033\payload" `
  -RequiredFiles @("scripts/release/Start-NrhisBuild.ps1")
```

Corrections must be applied to the extracted payload source before rerunning the
build.
