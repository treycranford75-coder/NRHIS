# ES-014 Sprint Archive Index

## Purpose

ES-014 defines discovery, validation, filtering, and export for immutable Sprint
archives.

## Discovery

Archive manifests are discovered recursively by locating
`sprint_archive_manifest.json`.

## Validation

Every discovered archive is validated through ES-013. Invalid archives remain
visible in the index with their validation errors.

## Filtering

Indexes may be filtered by:

- validation status;
- Sprint identifier stored in archive metadata.

## Export

The index may be exported as deterministic JSON for audit, release management,
or later automation.

## Preservation

Index generation is read-only and does not modify archives or the preserved
legacy Pass1 tree.
