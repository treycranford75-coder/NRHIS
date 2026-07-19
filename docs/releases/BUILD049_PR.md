## NRHIS Sprint 2 — Build049

Build049 adds repository-location safety to prevent OneDrive from interfering with Git internal files and tracked build payloads.

### Included

- Detect OneDrive-managed repository paths
- Create or update a protected clone at `C:\GitHub\NRHIS`
- Continue the same build automatically from the protected clone
- Copy and revalidate the Build049 ZIP and checksum
- Write external repository-migration evidence
- Preserve `develop`, no-prune synchronization, pre-push gates, publication, verification, archival, and next-build chaining

Build048 remains complete, published, verified, and archived.
