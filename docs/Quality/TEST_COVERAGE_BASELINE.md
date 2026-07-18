# NRHIS Test Coverage Baseline — Sprint 2 Build004

## Purpose

Build004 establishes an evidence-based automated coverage baseline for NRHIS and prevents future regression.

## Measurement

The baseline was measured on the Build003 release candidate using:

```powershell
python -m coverage erase
python -m coverage run --branch --source=src -m pytest -q
python -m coverage report -m --omit="src/nrhis_calibration/legacy/*"
```

Measured result:

- Tests: 13 passed
- Branch coverage: 82%
- Preservation-controlled legacy Pass1 tree: excluded

## Regression floor

The initial required floor is 80% branch coverage.

This floor is deliberately below the measured 82% baseline to tolerate minor platform differences while preventing meaningful regression.

## Exclusions

The following tree is excluded from coverage measurement:

```text
src/nrhis_calibration/legacy/*
```

The legacy Pass1 implementation is governed by the Build002 cryptographic preservation baseline and is not modern test-coverage scope.

## CI behavior

GitHub Actions now:

1. Installs `.[dev]`.
2. Runs Ruff.
3. Runs pytest with branch coverage.
4. Fails below 80%.
5. Produces terminal missing-line output.
6. Produces `coverage.xml`.
7. Uploads the XML report as a workflow artifact.

## Local commands

```powershell
python -m pytest -q --cov=src --cov-branch --cov-report=term-missing --cov-report=xml --cov-fail-under=80
```

## Future work

Later builds should raise coverage through focused tests for harvest error paths, registry validation, CLI behavior, service orchestration, and future domain modules. The threshold should only increase after a measured improvement is merged.
