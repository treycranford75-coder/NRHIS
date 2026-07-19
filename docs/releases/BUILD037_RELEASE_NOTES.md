## NRHIS Sprint 2 — Build037

Build037 turns the original root ZIP into a resumable, one-command lifecycle package.

### Automated lifecycle

- No-prune synchronization of `develop`
- Feature-branch creation or safe resumption
- Payload-authoritative installation and reruns
- PowerShell parser, Ruff, pytest/branch-coverage, and whitespace gates
- Complete staging, commit, and push
- Automatic pull-request creation against `develop`
- Automatic merge activation when repository policy permits
- Post-merge synchronization and exact merged-commit targeting
- Automatic pre-release publication through authenticated GitHub CLI
- Existing-release detection for safe reruns
- Exact tag-to-commit resolution through the GitHub API
- Normalized external evidence, evidence-index update, and completion receipt
- Automatic attachment of the original Build037 root ZIP when available

### Preserved controls

- `develop` remains the merge target
- Synchronization never prunes remote references
- Legacy Pass1 files are preserved
- Releases remain pre-releases and are not marked latest
- Verification fails closed on missing or inconsistent evidence
- Browser fallback remains available for unavoidable authorization or policy checkpoints

Build036 remains complete, published, and verified.
