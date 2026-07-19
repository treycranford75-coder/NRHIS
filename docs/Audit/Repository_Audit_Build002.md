# NRHIS Repository Audit — Sprint 2 Build002

## Document control

- Build: Sprint 2 Build002
- Branch: `feature/sprint2-build002`
- Baseline release: `v0.1.1-rc1+build001`
- Purpose: establish a documented repository baseline and preserve the legacy Pass1 calibration implementation.

## Repository status

NRHIS uses a Python `src/` package layout. The repository includes packages for calibration, core services, events, GIS, harvesting, publications, reservoirs, and water quality.

The USGS harvesting path was implemented in Build001. Several other domain packages remain early-stage or skeletal.

## Python and packaging

- Packaging configuration: `pyproject.toml`
- Source layout: `src/`
- Minimum Python version: `>=3.11`
- Build002 validation environment: Python 3.14
- Development installation:

```powershell
python -m pip install -e ".[dev]"
