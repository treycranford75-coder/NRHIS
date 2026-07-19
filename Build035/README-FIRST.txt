NRHIS Sprint 2 Build035 — One-Step Package

From the NRHIS repository root run:

  .\scripts\release\Start-NrhisBuild.ps1 -BuildNumber "035"

The existing permanent starter should locate this ZIP, extract Build035, and run Apply-Build035.ps1.
After PR checks pass and the PR is merged to develop:

  git switch develop
  git fetch origin --no-prune
  git pull --ff-only --no-prune origin develop
  .\Build035\Complete-Build035.ps1

Publish as a pre-release, not latest. Then run the generated verification-closure command with the public verification JSON evidence.
