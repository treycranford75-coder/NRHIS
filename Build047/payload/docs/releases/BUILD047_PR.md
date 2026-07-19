## NRHIS Sprint 2 — Build047

Build047 adds a pre-push CI parity gate to reduce avoidable remote CI failures.

### Included

- Run Ruff locally before push
- Compile Python sources and tests
- Run pytest with branch coverage and the 80% threshold
- Run `git diff --check`
- Write an external machine-readable parity receipt and full log
- Stop before commit/push when parity fails

Build046 remains complete, published, verified, and archived.
