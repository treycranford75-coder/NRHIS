# ES-004 Calibration Reference-Case Control

## Purpose

ES-004 defines the controlled manifest used to identify, hash, approve, and
validate calibration characterization artifacts.

## Required manifest fields

- `case_id`
- `implementation`
- `approved`
- `description`
- `artifacts`
- `ignored_json_keys`
- `csv_key_columns`
- `numeric_tolerances`

Each artifact records:

- relative path
- SHA-256 digest
- media type

## Approval rule

A reference case may exist in an unapproved state for development and review.
Production comparison must use `--require-approved` and must fail when the
manifest is not approved.

Changing an artifact after manifest creation invalidates the case because the
SHA-256 digest no longer matches.

## Build008 limitation

Build008 establishes reference-case control and validation. It does not mark
the synthetic Build007 fixtures as approved production records and does not
claim equivalence between legacy and modern implementations.
