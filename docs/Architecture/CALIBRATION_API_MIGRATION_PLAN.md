# NRHIS Calibration API and Migration Plan — Sprint 2 Build006

## Purpose

Build006 defines the stable public calibration interface and a controlled
migration path from preserved legacy Pass1 to future additive implementations.

## Public interface

- `CalibrationRunRequest`
- `CalibrationRunResult`
- `CalibrationRunner`
- `get_calibration_runner()`
- `run_calibration()`

The registered implementation is `legacy-pass1`.

## Current path

Caller -> public API -> registry -> legacy adapter -> Build005 compatibility
wrapper -> isolated subprocess -> preserved legacy Pass1.

## Migration stages

1. Preservation baseline — completed in Build002.
2. Isolated compatibility execution — completed in Build005.
3. Stable public API — completed in Build006.
4. Characterization fixtures and tolerance rules — planned.
5. Incremental additive modern modules — planned.
6. Dual-run comparison between legacy and modern implementations — planned.
7. Optional promotion of a modern default after documented approval.

Legacy retirement is not authorized by this plan.

## Stability guarantees

- No direct caller import from the legacy tree.
- No wrapper output written into the legacy tree.
- Unknown implementation names fail explicitly.
- Future runners use the same request and result contracts.
- Pre-existing legacy files remain unchanged.
