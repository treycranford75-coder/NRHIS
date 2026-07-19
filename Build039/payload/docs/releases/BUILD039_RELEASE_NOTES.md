## NRHIS Sprint 2 — Build039

Build039 introduces safe sequential build chaining after release verification is complete.

### Highlights

- Automatically starts the next build when its root ZIP is already available.
- Requires a verified completion receipt for the current build.
- Requires and validates the next ZIP's SHA-256 checksum.
- Stops cleanly rather than skipping a missing build.
- Includes loop protection and a `-NoChain` override.
- Preserves the complete Build038 one-step lifecycle and private-repository release verification.

This release is a pre-release and must not be marked as latest.
