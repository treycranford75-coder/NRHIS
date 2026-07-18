# ES-003 Calibration Characterization Standard

## Purpose

This standard defines how NRHIS records and compares calibration reference
artifacts before any modern implementation may claim compatibility with the
preserved legacy Pass1 process.

## Required reference package

Each approved characterization case must contain:

- documented input sources;
- immutable input hashes;
- expected metadata JSON;
- expected tabular outputs;
- implementation identifier;
- generation date and approval record;
- comparison keys;
- numeric tolerances and units;
- known exclusions and unresolved differences.

## Comparison rules

### Structure

JSON keys, sequence lengths, CSV columns, and keyed rows must match unless an
explicit exclusion is documented.

### Numeric values

Numeric differences must be evaluated with documented absolute or relative
tolerances. Zero tolerance is the default.

### Dynamic values

Timestamps, run identifiers, file paths, and other dynamic fields may only be
ignored when listed explicitly for the characterization case.

### Tables

Rows must use stable key columns. Duplicate keys are invalid. Ordering is not a
substitute for stable keys.

### Failure

Any missing row, unexpected row, missing key, unexpected key, type mismatch,
invalid numeric value, or tolerance exceedance fails characterization unless
reviewed and approved as a documented exception.

## Preservation

Characterization fixtures are additive. No pre-existing file under
`src/nrhis_calibration/legacy` may be modified to make a comparison pass.

## Build007 status

Build007 supplies the comparison framework and synthetic contract fixtures.
Production reference fixtures must be generated only from approved source
records and separately reviewed before acceptance.
