## NRHIS Sprint 2 — Build048

Build048 adds a workflow-contract preflight gate before the full local CI parity gate.

- Validates the permanent starter contract
- Runs targeted legacy workflow tests before full coverage
- Writes external preflight evidence
- Prevents known compatibility regressions from reaching GitHub CI
