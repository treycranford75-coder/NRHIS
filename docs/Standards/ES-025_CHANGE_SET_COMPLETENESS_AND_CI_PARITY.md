# ES-025 Change-Set Completeness and CI Parity

## Purpose

ES-025 prevents local corrections from being omitted from a build commit and
requires local validation to mirror the GitHub Actions release gates.

## Change-set completeness

Each build derives its expected files from the extracted payload and any
explicit compatibility files. Before commit, the staged change set must contain
every expected file and no unexpected repository file.

Installer folders, one-step ZIP files, and temporary starter scripts may remain
untracked during build application.

## CI parity

The local CI-parity gate runs:

- Ruff;
- the full pytest suite;
- branch coverage with the configured minimum;
- legacy preservation tests;
- Git whitespace validation.

A build may not be pushed until both the CI-parity gate and change-set
verification pass.
