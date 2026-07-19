NRHIS Sprint 2 Build038

Run from the NRHIS repository root:

  .\scripts\release\Start-NrhisBuild.ps1 -BuildNumber "038"

Build038 carries the authenticated GitHub CLI token into all private-repository
REST verification calls. The same resumable command installs, tests, commits,
pushes, creates/merges the PR when permitted, publishes the exact-commit
pre-release, verifies the tag, writes external evidence, and closes the receipt.

Permanent controls retained:
- develop merge target
- no-prune synchronization
- PowerShell syntax gate
- payload-authoritative reruns
- complete staging
- legacy preservation
- pre-release publication
- post-publication verification evidence
