# Sprint 2 Build001 Release Checklist

- [ ] Feature branch contains only intended Sprint 2 changes.
- [ ] `python -m pytest -q` passes.
- [ ] `python -m ruff check .` passes.
- [ ] `./scripts/Harvest-USGS.ps1 -StartDate 2026-07-17 -EndDate 2026-07-17` succeeds.
- [ ] Raw JSON exists and is valid JSON.
- [ ] Normalized CSV contains the expected stations, parameters, timestamps, units, and values.
- [ ] Metadata hashes match the generated artifacts.
- [ ] Operational log records a successful run.
- [ ] PR is reviewed and merged into `develop`.
- [ ] Release candidate tag `v0.1.1-rc1+build001` is created from the reviewed commit.
- [ ] Release notes identify the live smoke-test date and run ID.
