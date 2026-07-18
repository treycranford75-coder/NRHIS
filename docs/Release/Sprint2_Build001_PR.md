# Pull Request: Sprint 2 USGS Harvest Engine Build001

## Summary

Implements the first operational NRHIS USGS NWIS harvest path for release candidate
`v0.1.1-rc1+build001`.

## Changes

- Adds `scripts/Harvest-USGS.ps1` as the Windows operational entry point.
- Adds configuration-driven station loading and validation.
- Downloads USGS NWIS Instantaneous Values JSON.
- Preserves immutable raw JSON under a UTC run identifier.
- Emits a stable normalized CSV observation schema.
- Records request provenance, date coverage, counts, registry hash, and artifact hashes.
- Writes console and file logs and returns nonzero on controlled failures.
- Adds unit tests, an operational runbook, and ES-002 provenance requirements.

## Verification

- `python -m pytest -q` — 7 passed.
- Ruff was not available in the isolated review runtime; run `python -m ruff check .` in the
  configured development environment before merge.
- Conduct one live USGS smoke test before tagging the release candidate.

## Merge target

`feature/sprint2-usgs-harvest` -> `develop`

## Release gate

Do not tag until automated tests, Ruff, and one live lower Nueces harvest all pass and the raw,
normalized, metadata, and log artifacts have been visually inspected.
