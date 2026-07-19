NRHIS Sprint 2 Build045

From the NRHIS repository root, run:

  .\scripts\release\Start-NrhisBuild.ps1 -BuildNumber "045"

The same command is resumable. If required GitHub checks remain blocked after the wait window, Build045 writes diagnostic evidence, opens the pull request, and stops safely. After correcting the check, rerun the same command.
