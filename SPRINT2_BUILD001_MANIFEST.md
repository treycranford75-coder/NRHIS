# NRHIS Sprint 2 Build001 Implementation Manifest

Target branch: `feature/sprint2-usgs-harvest`

Release candidate: `v0.1.1-rc1+build001`

Local verification completed in the review environment:

```text
7 passed
```

Ruff was not installed in the review environment and remains a required local release gate.
A live USGS request also remains a required release gate because the review runtime did not use
external network access.

Apply this package over the repository root while the target feature branch is checked out. Then
run the commands listed in `docs/Release/Sprint2_Build001_Release_Checklist.md`.
