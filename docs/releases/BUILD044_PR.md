## NRHIS Sprint 2 — Build044

Build044 modernizes the release-workflow regression tests so harmless script refactoring no longer breaks CI.

### Included

- Replace legacy exact-substring assertions with behavior-oriented checks
- Verify ZIP discovery, extraction, repository-root protection, checksum validation, extraction reuse, and apply-script execution
- Preserve native Git exit-code handling from Build043
- Preserve no-prune synchronization, automated publication, verification, archival, and chaining
- Emit the standard completion prompt: `lets move on to next build`

Build043 remains complete, published, verified, and archived.
