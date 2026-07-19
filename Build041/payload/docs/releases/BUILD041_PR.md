## NRHIS Sprint 2 — Build041

Build041 adds safe installer-artifact archival after the release completion gate.

### Included

- Requires a verified Build041 completion receipt before archival
- Archives the Build041 folder, original root ZIP, and checksum outside the repository
- Creates a machine-readable archive manifest with per-file SHA-256 hashes
- Records the final archive SHA-256
- Preserves all Git-tracked installer and legacy artifacts
- Removes only known untracked `.previous` and temporary extraction remnants
- Supports `-NoArchive` as an explicit opt-out
- Performs next-build chaining only after archival succeeds
- Retains expanded package discovery, resumable extraction, no-prune synchronization, automated PR/merge, pre-release publication, authenticated verification, and evidence closure

Build040 remains complete, published, and verified.
