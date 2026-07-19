NRHIS SPRINT 2 - BUILD037 ONE-STEP ROOT ZIP

Run from the NRHIS repository root:

  .\scripts\release\Start-NrhisBuild.ps1 -BuildNumber "037"

Build037 uses the same command as a resumable lifecycle controller. It installs and validates the payload, creates and pushes the branch, creates the PR, enables auto-merge when GitHub permits it, waits for merge, publishes the exact-commit pre-release, closes verification, and confirms the completion receipt.

A one-time GitHub CLI web authorization may appear. Complete that authorization once; later builds can run without the browser authorization step.

If repository policy or missing authorization requires a browser action, complete the displayed PR or release step and rerun the same Start-NrhisBuild command. The workflow resumes from the completed checkpoint without rebuilding or pruning.

Manual continuation alias:

  .\Build037\Complete-Build037.ps1

Permanent safeguards retained:
- develop merge target
- no-prune synchronization
- PowerShell syntax validation
- payload-authoritative reruns
- complete staging
- legacy preservation
- pre-release publication
- exact tag-to-commit verification
- external evidence index and completion receipt
