## NRHIS Sprint 2 - Build091

Build091 permanently fixes the missing completion-wrapper failure exposed after Build090 merged and prevents duplicate lifecycle chaining after a self-contained build completes.

### Included

- Adds `scripts/release/New-NrhisCompletionWrapper.ps1`.
- Updates `Invoke-NrhisSelfContainedBuild.ps1` to generate the wrapper before staging.
- Automatically includes the generated wrapper in the explicit staging allowlist.
- Records the effective staged paths in the completion receipt.
- Validates wrapper syntax and the `-RepositoryRoot` contract.
- Updates `Start-NrhisBuild.ps1` to stop cleanly when a self-contained child already wrote its closure receipt and returned to `develop`.
- Adds deterministic regression tests for generation, staging, lifecycle consumption, and duplicate-chain prevention.

### Result

Future builds remain resumable after merge, and a successful self-contained build does not trigger a second legacy PR/lifecycle sequence.
