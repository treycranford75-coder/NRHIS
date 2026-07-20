# Build063 Operations-Cycle Reliability

Build063 converts the fixes validated during the Build062 live runs into permanent production behavior.

- Current USGS harvest retries transient failures up to three times with bounded exponential backoff.
- Incremental USGS harvesting defaults to a recent two-day source window rather than replaying the historical study period.
- Operational child processes cannot request interactive input.
- Each step is limited by the configured timeout and records exit code 124 when exceeded.
- Repository and output paths are resolved after PowerShell parameter binding, preventing empty-path failures.
