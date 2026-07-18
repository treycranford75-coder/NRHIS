# NRHIS — Development Plan (analysis pass)

Summary
-------
NRHIS is a Python-based hydrologic system with modular packages for calibration, core services, events, GIS, harvesting, publications, reservoirs, and water quality. The repository currently includes a legacy Pass1 calibration implementation that must be preserved under src/nrhis_calibration/legacy.

Observed repository layout (top-level)
--------------------------------------
- .gitignore
- CHANGELOG.md
- CONTRIBUTING.md
- LICENSE
- README.md
- archive/
- config/
- data/
- docs/
- events/
- gis/
- pyproject.toml
- reports/
- scripts/
- src/
- tests/

Source layout (src/)
--------------------
- src/nrhis_calibration/
  - __init__.py
  - legacy/
    - calibrate_pass1.py
    - MIGRATION_MANIFEST.txt
    - README.txt
    - Run_Pass1.bat
    - run_pass1.ps1
  - (no modern calibration module present yet)
- src/nrhis_core/
  - __init__.py
- src/nrhis_events/
  - __init__.py
- src/nrhis_gis/
  - __init__.py
- src/nrhis_harvest/
  - __init__.py
- src/nrhis_publications/
  - __init__.py
- src/nrhis_reservoirs/
  - __init__.py
- src/nrhis_waterquality/
  - __init__.py

What I inspected
-----------------
- Top-level directory listing and existence of pyproject.toml.
- The src tree and each package's __init__.py files (small placeholders).
- src/nrhis_calibration/legacy contents: a sizable calibrate_pass1.py plus Windows batch and PowerShell runners and migration manifest and README. This legacy code appears to implement an older "Pass1" calibration flow and must be preserved unchanged under legacy/.

Key observations and risks
--------------------------
- Several packages exist but currently contain only package initializers; implementation appears fragmented or in early stages.
- The legacy Pass1 calibration code is present and non-trivial; it must not be removed or altered.
- No CI/workflow files were enumerated in the scan — repository health depends on adding automated checks.
- pyproject.toml is present (use it to discover the build/packaging tool and dependencies). The repository's runnable entrypoints and dependency list have not been fully parsed yet.
- Tests/ directory exists, but test coverage and integration with the codebase are unknown without running them.
- Data/, config/, docs/ and scripts/ need inventory and standardization to ensure reproducible runs.

Recommended next implementation steps (prioritized)
--------------------------------------------------
Notes: these recommendations preserve all existing files and do not modify code. They are ordered so early steps are low-risk, investigation-first activities.

1) Immediate repository audit (non-editing)
   - Open and record pyproject.toml contents to determine packaging tool (setuptools/poetry/flit) and exact dependency list + Python version.
   - Read README.md, docs/, and tests/ to find the primary entrypoint(s) and runtime expectations (CLI, services, batch).
   - Inventory scripts/, data/, config/ to locate required external inputs and example datasets.
   - Confirm that src/nrhis_calibration/legacy files are executable as-is and note any external dependencies they require.

2) Developer experience and environment (low effort)
   - Add a CONTRIBUTING / DEV_SETUP section in docs (or expand the existing CONTRIBUTING.md) describing: Python version, how to create a venv, how to install dependencies from pyproject.toml, and how to run tests locally.
   - Create a reproducible dev environment (documented only at this stage): venv/poetry/pipx steps and explicit commands to run unit tests.

3) Continuous integration (medium effort)
   - Add GitHub Actions (or preferred CI) to run linting, unit tests, and type checks on PRs.
   - Start with minimal pipeline: install deps, run tests, run flake8/ruff or black format check.
   - Ensure CI does not modify repository files (read-only checks).

4) Tests and coverage (medium → high effort)
   - Run existing test suite and identify gaps. Prioritize adding unit tests for core behavior in nrhis_core and for any modules with non-trivial logic.
   - Add lightweight integration tests for the calibration flow that do not alter legacy source (e.g., run legacy scripts in a sandboxed environment or validate expected outputs using sample data).

5) Encapsulation strategy for calibration (design work)
   - Do not modify legacy code. Design a new calibration API layer that:
     - Wraps the legacy Pass1 scripts (call them as external/isolated processes or import them in a compatibility wrapper).
     - Provides a clean, documented interface for future modern implementations.
   - Create an explicit migration plan (mapped to MIGRATION_MANIFEST.txt) that outlines the sequence for incrementally porting functionality from legacy/calibrate_pass1.py into new modules, with tests for each ported piece.

6) Modularization and APIs (medium → high effort)
   - Define clear public interfaces for:
     - Core services (nrhis_core)
     - Event ingestion/processing (nrhis_events)
     - GIS-related utilities (nrhis_gis)
     - Data harvest and ETL (nrhis_harvest)
     - Reservoir and water quality models
   - For each package, produce a short design doc (one page) stating responsibilities, inputs/outputs, and stability guarantees.

7) Data management and reproducibility (medium effort)
   - Standardize config/ and data/ layouts (separate raw/processed and include README explaining expected files).
   - Add sample datasets (or pointer to external data) for CI tests that are small and deterministic.

8) Observability and releases (low → medium effort)
   - Add logging conventions and configuration (centralize logger setup in nrhis_core).
   - Define release process; tie CHANGELOG.md to GitHub Releases.

Deliverables to produce first (no code changes)
-----------------------------------------------
- DEVELOPMENT_PLAN.md (this document) at repo root.
- A short repository audit report listing:
  - pyproject.toml dependency and Python version (after inspection)
  - existing test status (tests passing / failing)
  - a mapping of which top-level scripts depend on which data/config files
- Minimal CI workflow that only runs (proposed files, do not commit yet) — a draft YAML to review.

Preservation requirements
------------------------
- Keep every existing file unchanged.
- Preserve src/nrhis_calibration/legacy exactly where it is and do not remove or refactor Pass1 files.
- Any new calibration implementation must be additive (new package/module), and must interoperate with the legacy code through a compatibility layer until the legacy implementation is fully validated and optionally retired.

Questions to clarify next
-------------------------
1. Which Python versions and packaging tool should be considered authoritative (pyproject lists candidates — confirm the target)?
2. Is the legacy Pass1 considered "reference truth" (must remain runnable indefinitely) or is it acceptable to reimplement and deprecate it after verification?
3. Do you have a CI preference (GitHub Actions is typical) and any constraints for running integration tests that use larger datasets or external services?

Appendix: quick inventory notes
------------------------------
- The legacy calibration script (src/nrhis_calibration/legacy/calibrate_pass1.py) is substantive and is accompanied by runners for Windows (.bat and PowerShell). Treat it as an executable artifact.
- Many packages under src/ are skeletons (only __init__.py present). This suggests the repository is organized by domain but implementation is partial or split across other folders (archive/, scripts/, or reports/).
- pyproject.toml exists and should be the first source of truth for dependency resolution.

Prepared by: lead engineer (analysis pass)
Date: 2026-07-18