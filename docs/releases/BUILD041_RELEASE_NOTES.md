## NRHIS Sprint 2 — Build041

Build041 adds verified post-completion archival of installer artifacts to the automated one-step lifecycle.

### Included

- Completion-receipt-gated installer archival
- External ZIP archive of the build folder and root package files
- Machine-readable archive manifest with SHA-256 evidence
- Preservation of all Git-tracked and legacy artifacts
- Cleanup limited to known untracked transient extraction remnants
- `-NoArchive` opt-out
- Safe next-build chaining after archive verification
- Existing automated discovery, extraction reuse, PR, merge, pre-release, release verification, evidence index, and receipt controls retained

This release is a pre-release and is not the latest production release.
