# ES-029 Payload Consistency and Complete Staging

## Purpose

ES-029 prevents a corrected working-tree file from diverging from its extracted
payload source and prevents required build files from being omitted during
staging.

## Payload consistency

Before CI-parity validation, every extracted payload file is compared with its
installed working-tree counterpart using SHA-256.

A mismatch blocks the build and identifies the affected file. Corrections must
be made in the payload source so reruns cannot overwrite them.

## Complete staging

The staging helper combines:

- every file discovered in the extracted payload;
- explicitly declared additional files;
- explicitly required permanent workflow files.

The complete expected set is staged and verified before commit.
