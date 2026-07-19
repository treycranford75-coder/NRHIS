# ES-008 Calibration Reference Comparison Control

## Purpose

ES-008 defines the controlled comparison of candidate calibration artifacts
against approved reference cases.

## Approval requirement

Approved reference cases are required by default. Unapproved cases may be used
only for development with an explicit override.

## Comparison behavior

- JSON artifacts use structural comparison and ignored-key controls.
- CSV artifacts use stable key columns and numeric tolerances.
- Other files use exact byte comparison.
- Missing candidate artifacts are recorded as failures.
- Every difference includes a location and reason.

## Result

A comparison passes only when every artifact matches.

## Reporting

Comparison results may be exported as deterministic JSON for review, CI, or
release evidence.

## Preservation

Comparison is read-only and does not modify reference cases, candidate
artifacts, or preserved legacy Pass1 files.
