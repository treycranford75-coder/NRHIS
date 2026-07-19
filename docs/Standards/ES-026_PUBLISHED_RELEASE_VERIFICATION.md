# ES-026 Published Release Verification

## Purpose

ES-026 verifies that the public GitHub release matches the approved NRHIS
release metadata after publication.

## Required verification

The verifier confirms:

- exact release tag;
- exact release title;
- pre-release status;
- non-draft status;
- exact Markdown release notes;
- published release URL.

## Evidence

A machine-readable JSON evidence record is written outside the repository under:

`%LOCALAPPDATA%\NRHIS\release-evidence`

The evidence record includes expected values, actual GitHub values, individual
check results, verification time, and overall pass/fail status.

## Access method

Verification uses GitHub's public REST API and does not require GitHub CLI
authentication for the public NRHIS repository.
