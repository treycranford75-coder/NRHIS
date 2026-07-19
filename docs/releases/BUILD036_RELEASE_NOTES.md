## NRHIS Sprint 2 — Build036

Build036 automates the post-merge release lifecycle and verification closure.

### Included in this build
- One-command post-merge synchronization, publication, verification, and closure
- Automatic GitHub CLI pre-release publication when authenticated
- Exact tag-to-merged-commit resolution through the GitHub API
- Normalized external release-verification evidence
- Automatic completion receipt and evidence-index validation
- Optional upload of the original one-step ZIP as a release asset
- Browser publication fallback with automatic resume on rerun
- Whitespace-safe commit verification

### Permanent workflow controls retained
- Merge target remains `develop`
- No-prune synchronization
- PowerShell syntax gate
- Ruff and full pytest validation
- Branch coverage requirement of at least 80%
- Payload-authoritative reruns and complete staging
- Legacy Pass1 preservation
- Pre-release publication; not marked latest
- Post-publication verification evidence stored outside the repository
