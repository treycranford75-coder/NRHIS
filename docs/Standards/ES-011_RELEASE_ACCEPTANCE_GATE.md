# ES-011 Calibration Release Acceptance Gate

## Purpose

ES-011 defines the final machine-readable acceptance gate for calibration
release evidence.

## Required checks

The gate verifies:

- evidence-bundle integrity;
- presence of `dual_run_summary.json`;
- presence of `comparison_report.json`;
- successful comparison outcome.

## Acceptance rule

A release is accepted only when every required check passes.

A failed check produces a nonzero command exit status and a deterministic JSON
report suitable for CI and release records.

## Development override

A comparison mismatch may be allowed only through an explicit development
override. Such a result is not valid production release evidence.

## Preservation

The release gate is read-only and does not modify evidence artifacts, approved
reference cases, or the preserved legacy Pass1 tree.
