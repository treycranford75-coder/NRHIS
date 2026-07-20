# Build071 Automatic Pull Requests

Build071 closes the recurring lifecycle gap where a build stopped after pushing its feature branch and instructed the operator to create a pull request manually.

`Start-NrhisBuild.ps1` now verifies and extracts the package, runs the build, then automatically creates or reuses a pull request from `feature/sprint2-build###` into `develop`.

The helper fails clearly when GitHub CLI is unavailable or unauthenticated. Use `-SkipPullRequest` only for deliberate offline or diagnostic runs.
