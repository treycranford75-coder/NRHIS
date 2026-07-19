# ES-005 Calibration Reference Capture Workflow

## Purpose

ES-005 defines how a successful calibration run is copied into a controlled,
immutable, unapproved reference-case package.

## Capture prerequisites

- the source run directory exists;
- `metadata.json` exists and is valid JSON;
- `return_code` equals zero;
- `succeeded` equals true;
- required stdout and stderr artifacts exist;
- the destination case identifier is unique.

## Capture output

Each case contains:

- `case.json`
- `capture_record.json`
- `artifacts/metadata.json`
- `artifacts/stdout.log`
- `artifacts/stderr.log`

All listed artifacts are hashed through the Build008 manifest controls.

## Approval separation

Capture never approves a case. Every captured case is written with:

```text
approved: false
```

Approval requires a separate review and promotion action in a later controlled
workflow.

## Immutability

An existing reference-case directory is never overwritten. A changed case must
use a new case identifier.

## Preservation

Capture is additive and does not modify the preserved legacy Pass1 tree.
