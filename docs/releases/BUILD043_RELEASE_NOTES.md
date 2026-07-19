## NRHIS Sprint 2 — Build043

Build043 permanently fixes PowerShell native-command handling for Git operations.

### Included

- Normal Git progress on stderr is logged without being treated as failure
- Git exit codes remain the sole success/failure authority
- Locked-directory retry prompts continue to receive automatic `n` responses
- Full automated PR, merge, pre-release, verification, archival, and chaining lifecycle retained

This release is a pre-release and must not be marked as latest.
