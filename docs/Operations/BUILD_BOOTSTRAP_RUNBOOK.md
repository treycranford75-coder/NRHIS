# Build Bootstrap Runbook

Run any future build from the NRHIS repository root with:

```powershell
.\scriptselease\Start-NrhisBuild.ps1 -BuildNumber "026"
```

The starter locates and extracts the matching ZIP automatically.

If the generic starter has not yet been merged, use the temporary starter
included with the build package:

```powershell
.\Start-NRHIS-Build026.ps1
```

After the pull request is merged, run the build-specific completion script.
Temporary starter files are removed automatically during completion.
