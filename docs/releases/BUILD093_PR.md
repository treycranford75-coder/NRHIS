## NRHIS Sprint 2 - Build093

### Installer archive lifecycle guard

- fixes the malformed `Test-Path ... -and Test-Path ...` expression exposed by Build092;
- preserves the existing installer packaging and evidence-archive contract;
- adds deterministic regression coverage for the exact PowerShell guard;
- makes no production USGS historical requests.

After release closeout, operations return to the Build092 eight-station historical USGS bootstrap plan.
