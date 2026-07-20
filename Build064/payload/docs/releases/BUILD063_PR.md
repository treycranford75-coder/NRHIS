## NRHIS Sprint 2 — Build063

Build063 incorporates the operational fixes proven during Build062 live-cycle testing.

### Included
- Runtime-safe `RepositoryRoot` and `OutputRoot` initialization for USGS wrappers
- Three-attempt USGS current-harvest retry with exponential backoff
- Recent two-day default window for incremental USGS updates
- Noninteractive PowerShell child execution
- Configurable five-minute per-step timeout
- Exit code 124 and persisted log evidence when a step times out
- Build063 cycle receipts recording the active timeout

Build062 remains complete, published, verified, and archived.
