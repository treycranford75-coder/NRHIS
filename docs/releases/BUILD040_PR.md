## NRHIS Sprint 2 — Build040

Build040 hardens the original root-ZIP lifecycle.

### Included

- Searches repository roots, Downloads, OneDrive Downloads, Desktop, and OneDrive Desktop
- Prints every package-search location
- Verifies the companion SHA-256 before use
- Copies verified ZIP and checksum into the NRHIS root automatically
- Reuses checksum-matched extraction on reruns
- Uses temporary extraction and safe folder replacement
- Removes the trailing-blank-line packaging defect
- Disables interactive Git credential prompts and retries transient Windows lock failures once
- Preserves no-prune synchronization and all existing release gates

Build039 remains complete, published, and verified.
