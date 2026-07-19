# ES-009 Calibration Dual-Run Verification

## Purpose

ES-009 defines the controlled execution and comparison sequence used to verify
candidate calibration behavior against an approved reference case.

## Required sequence

1. Load the selected implementation through the Build006 public API.
2. Execute the calibration run through the controlled runner boundary.
3. Require a successful return code before comparison.
4. Locate the candidate artifacts from the generated run metadata path.
5. Compare the candidate artifacts through the Build012 comparison controls.
6. Write a deterministic comparison report.
7. Return failure when any artifact differs.

## Approval requirement

Approved reference cases are required by default. An unapproved case may only be
used with an explicit development override.

## Release evidence

A release-quality dual-run record includes:

- run identifier;
- implementation;
- approved reference-case identifier;
- calibration return code;
- comparison outcome;
- comparison-report path;
- deterministic JSON summary.

## Preservation

Dual-run verification is additive and does not modify the approved reference
case or the preserved legacy Pass1 tree.
