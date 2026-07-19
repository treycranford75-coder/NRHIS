## NRHIS Sprint 2 — Build042

Build042 eliminates the recurring Windows/OneDrive directory-deletion question from the one-step lifecycle.

### Included

- Automatically declines Git for Windows `Should I try again? (y/n)` deletion retries
- Supplies enough noninteractive `n` responses for multiple locked directories
- Preserves the original Git output as execution evidence
- Retains the existing two-attempt transient Git retry
- Stops only when a required Git command actually remains unsuccessful
- Does not prune branches or remote-tracking references
- Does not delete tracked installer, payload, evidence, or legacy files
- Retains automated discovery, checksum validation, resumable extraction, PR creation, auto-merge, pre-release publication, authenticated verification, archival, and next-build chaining

Build041 remains complete, published, verified, and archived.
