# ES-010 Calibration Release Evidence Bundle

## Purpose

ES-010 defines the immutable evidence package used to preserve calibration
verification outputs for review, release, and audit.

## Required bundle contents

A bundle contains:

- `evidence_manifest.json`;
- copied evidence artifacts under `artifacts/`;
- release or review metadata;
- SHA-256 digest and byte size for every artifact.

## Immutability

Existing bundle identifiers are never overwritten. A corrected bundle must use
a new identifier.

## Validation

Validation fails when:

- the manifest is missing or malformed;
- an artifact is missing;
- an artifact size differs;
- an artifact SHA-256 digest differs;
- the artifact list is empty.

## Recommended evidence

- dual-run summary;
- comparison report;
- reference-case manifest;
- approval record;
- CI result export;
- release checklist.

## Preservation

Evidence bundling is additive and does not modify source artifacts, approved
reference cases, or the preserved legacy Pass1 tree.
