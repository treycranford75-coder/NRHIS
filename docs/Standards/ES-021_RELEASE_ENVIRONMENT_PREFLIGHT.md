# ES-021 Release Environment Preflight

## Purpose

ES-021 defines preflight checks for the NRHIS release environment and controlled
GitHub CLI bootstrap.

## Required checks

- Git is installed.
- Python is installed.
- The repository is the expected NRHIS repository.
- The active branch matches the required branch.
- The working tree is clean.

GitHub CLI installation and authentication may be required for fully automated
pull-request and release publication.

## Installation control

GitHub CLI installation must occur only when the operator explicitly supplies
the `-Install` switch. Authentication must occur only when the operator
explicitly supplies the `-Authenticate` switch.
