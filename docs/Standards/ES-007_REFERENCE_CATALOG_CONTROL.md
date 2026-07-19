# ES-007 Calibration Reference Catalog Control

## Purpose

ES-007 defines how approved and unapproved calibration reference cases are
discovered, validated, filtered, and exported as a catalog.

## Catalog requirements

Each catalog entry records:

- case identifier;
- implementation;
- approval state;
- description;
- manifest path;
- artifact count;
- validation status;
- validation error, when applicable.

## Discovery

Reference cases are discovered recursively by locating `case.json` manifests.

## Validation

Every discovered case is validated through the Build008 controls. Invalid
cases remain visible in the catalog and are marked invalid rather than silently
discarded.

## Filtering

Catalogs may be filtered by:

- implementation;
- approved state;
- valid state.

## Export

Catalogs may be exported as deterministic JSON for audit, review, or later
automation.

## Preservation

Catalog generation is read-only and does not modify reference cases or the
preserved legacy Pass1 tree.
