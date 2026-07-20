# Build083: integrate TexasET with reservoir evaporation reporting

## Summary
- Converts Coastal Bend and Winter Garden reference ETo into configurable reservoir evaporation ranges.
- Reports acre-feet/day and MGD for Lake Corpus Christi and Choke Canyon Reservoir.
- Preserves the distinction between reference ETo and direct open-water evaporation.
- Adds deterministic tests and operational documentation.

## Validation
- Build083 deterministic tests pass.
- Completion wrapper accepts `-RepositoryRoot`.
