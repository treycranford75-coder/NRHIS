# Calibration Characterization Harness — Sprint 2 Build007

## Scope

Build007 implements reusable JSON and CSV comparison utilities for future
side-by-side verification of preserved legacy Pass1 and additive modern
calibration implementations.

## Components

- `src/nrhis_calibration/characterization.py`
- synthetic contract fixtures under `tests/fixtures/calibration_characterization`
- automated characterization tests
- ES-003 characterization standard

## Important limitation

The included fixtures are synthetic contract fixtures. They validate the
comparison machinery but are not approved production reference outputs.

Production characterization begins only after approved legacy inputs and
outputs are captured, hashed, reviewed, and entered into a controlled fixture
package.

## Comparison capabilities

- SHA-256 artifact hashing
- JSON structural comparison
- explicit ignored JSON keys
- absolute and relative numeric tolerances
- CSV loading
- stable multi-column row keys
- row and column difference reporting
- duplicate-key rejection

## Next migration gate

A later build may use this harness to create approved reference cases and
perform dual-run comparison. Build007 does not claim modern equivalence.
