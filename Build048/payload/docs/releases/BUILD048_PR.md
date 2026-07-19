## NRHIS Sprint 2 — Build048

Build048 prevents legacy workflow-contract regressions from reaching the full parity gate or GitHub CI.

### Included

- Validate permanent starter behavior before the full CI parity run
- Run targeted workflow contract tests first
- Require the runtime apply-script path contract
- Write preflight evidence and a machine-readable receipt
- Stop before commit or push when the contract gate fails

### Controls retained

- Merge target remains `develop`
- No-prune synchronization
- Payload-authoritative reruns
- Complete staging and legacy preservation
- Automated PR, merge, pre-release, verification, archival, and next-build chaining

Build047 remains complete, published, verified, and archived.
