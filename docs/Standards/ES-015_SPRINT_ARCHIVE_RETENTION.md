# ES-015 Sprint Archive Retention

ES-015 defines non-destructive retention planning for immutable Sprint archives.

Each archive is classified as `retain`, `review`, or `quarantine`. The configured
number of latest valid archives is retained, older valid archives are marked for
review, and invalid archives are marked for quarantine.

Retention planning never deletes, moves, or modifies archives. Plans may be
exported as deterministic JSON for review and later controlled automation.
