# ES-027 PowerShell Syntax and No-Prune Synchronization

## Purpose

ES-027 prevents malformed PowerShell release scripts from reaching GitHub and
prevents automatic Git pruning from producing interactive deletion prompts on
Windows and OneDrive workspaces.

## PowerShell syntax gate

Every script under `scripts/release` is parsed with the native PowerShell parser
before Ruff, pytest, coverage, and legacy-preservation validation.

Any parser error blocks the build before commit and push.

## Repository synchronization

Build application and release completion synchronize `develop` with:

- `git fetch origin --no-prune`
- `git pull --ff-only --no-prune origin develop`

Automatic pruning is prohibited in the one-step workflow. Stale references may
be cleaned separately during planned maintenance.
