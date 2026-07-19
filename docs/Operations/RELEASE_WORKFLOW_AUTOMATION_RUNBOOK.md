# Release Workflow Automation Runbook

## Prerequisites

Git and Python are required. GitHub CLI is optional but recommended.

Authenticate GitHub CLI once:

```powershell
gh auth login
```

## Build application and pull request

Each one-step package runs its `Apply-Build###.ps1` script. The script installs
the payload, validates it, commits it, pushes the feature branch, and creates the
pull request when GitHub CLI is available.

Merging remains manual after all GitHub checks pass.

## Post-merge completion

Run the build-specific `Complete-Build###.ps1` script. It updates `develop`,
reruns all release gates, removes installer artifacts, creates and pushes the
annotated tag, and publishes the GitHub pre-release when GitHub CLI is
authenticated.
