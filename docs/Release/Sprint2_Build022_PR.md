## Summary

Adds dry-run simulation for approved archive-retention action manifests.

## Changes

- Accepts validated dry-run action manifests only.
- Produces simulated retain, review, and quarantine outcomes.
- Writes deterministic execution-report JSON.
- Requires `dry_run: true` and `executed: false`.
- Rejects live action manifests.
- Performs no archive deletion, movement, quarantine, or modification.
- Adds an execution-simulation CLI, tests, ES-018, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Simulation, live-manifest rejection, report validation, and CLI behavior are tested.

## Merge target

`feature/sprint2-build022` -> `develop`
