## Build096: harden finalized-history query CLI

This build makes the Build095 local historical query interface reliable when invoked directly from the repository and through `powershell.exe -File`.

### Changes
- Bootstrap `src` in `scripts/query_usgs_history.py` before importing `nrhis_analysis`.
- Normalize comma-delimited `SiteNo` and `ParameterCode` values into dedicated arrays in the PowerShell wrapper.
- Add deterministic regression tests for both CLI contracts.
- Preserve the local-only, zero-USGS-request query model.

No historical archive data is changed by this build.
