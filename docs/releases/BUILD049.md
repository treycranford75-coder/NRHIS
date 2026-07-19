# NRHIS Sprint 2 Build049

Build049 protects the release lifecycle from OneDrive interference by moving active Git execution to a non-synced working tree.

## Included

- Detect a repository path managed by OneDrive.
- Clone or update the authoritative `develop` branch at `C:\GitHub\NRHIS`.
- Copy the verified root ZIP and checksum to the protected working tree.
- Continue the same Build049 lifecycle automatically after migration.
- Write an external machine-readable repository-migration receipt.
- Preserve no-prune synchronization and all existing publication, verification, archival, and chaining gates.
