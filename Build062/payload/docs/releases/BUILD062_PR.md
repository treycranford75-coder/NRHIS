## NRHIS Sprint 2 — Build062

Build062 adds the twice-daily NRHIS operations-cycle runner.

### Included

- Fixed operational sequence from source harvest through publication bundle
- Required-step fail-fast behavior
- Individual step logs and exit codes
- Timestamped cycle receipt and latest-cycle pointer
- Morning/evening cycle naming support
- Publication authorization only after a successful cycle and two completed QA passes
- Deterministic tests for sequencing, failure blocking, missing scripts, and QA forwarding

Build061 remains complete, published, verified, and archived.
