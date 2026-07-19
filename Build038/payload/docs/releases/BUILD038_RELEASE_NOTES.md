## NRHIS Sprint 2 — Build038

Build038 authenticates all GitHub REST verification calls for private-repository
operation and removes the manual release-evidence workaround encountered in
Build037.

### Improvements

- Uses the active GitHub CLI token for release and tag API calls
- Resolves lightweight and annotated tags through authenticated requests
- Normalizes full commit SHAs before authoritative comparison
- Preserves exact-commit pre-release publication
- Automatically writes verification evidence and the completion receipt

This is a pre-release and must not be marked as the latest release.
