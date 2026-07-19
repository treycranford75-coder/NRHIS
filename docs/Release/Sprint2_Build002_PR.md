# NRHIS Repository Audit — Sprint 2 Build002

## Document control

- Build: Sprint 2 Build002
- Branch: `feature/sprint2-build002`
- Baseline release: `v0.1.1-rc1+build001`
- Purpose: establish a documented repository baseline and preserve the legacy Pass1 calibration implementation.

## Repository status

NRHIS is organized as a Python package using a `src/` layout. The repository includes domain packages for calibration, core services, events, GIS, harvesting, publications, reservoirs, and water quality.

The operational USGS harvesting path was implemented in Build001. Most other domain packages remain early-stage or skeletal.

## Python and packaging

- Packaging configuration: `pyproject.toml`
- Source layout: `src/`
- Authoritative minimum Python version: `>=3.11`
- Local validation environment used for Build002: Python 3.14
- Installation command:

```powershell
python -m pip install -e ".[dev]"

@'
# Sprint 2 Build002 Pull Request

## Summary

Establishes the NRHIS repository audit and cryptographic preservation baseline for the legacy Pass1 calibration implementation.

## Changes

- Adds the approved root-level `DEVELOPMENT_PLAN.md`.
- Adds the Build002 repository audit.
- Adds a SHA-256 manifest covering the preserved legacy Pass1 tree.
- Adds automated tests that detect missing, altered, or unmanifested legacy files.
- Adds the Build002 release checklist.
- Makes no functional change to the legacy Pass1 implementation.

## Verification

- Legacy preservation tests: 3 passed
- Full test suite: 10 passed
- Ruff: all checks passed
- Git diff whitespace validation: passed

## Merge target

`feature/sprint2-build002` → `develop`

## Preservation requirement

The legacy Pass1 implementation remains additive-only and must not be modified, removed, renamed, or refactored without a separately approved migration and verification plan.
