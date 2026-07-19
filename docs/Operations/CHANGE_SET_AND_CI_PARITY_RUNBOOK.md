# Change-Set and CI-Parity Runbook

Run local CI parity:

```powershell
.\scriptselease\Invoke-NrhisCiParity.ps1 -MinimumCoverage 80
```

Verify a staged build change set:

```powershell
.\scriptselease\Test-NrhisBuildChangeSet.ps1 `
  -ExpectedFiles $ExpectedFiles
```

The verifier blocks:

- expected files that were not staged;
- expected files that remain unstaged;
- unexpected staged files;
- unexpected untracked files.
