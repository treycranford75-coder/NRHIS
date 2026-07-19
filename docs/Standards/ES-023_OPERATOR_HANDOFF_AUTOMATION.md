# ES-023 Operator Handoff Automation

## Purpose

ES-023 defines a single, durable handoff package for each NRHIS pull request and
release.

## Required handoff contents

- pull-request base branch;
- pull-request compare branch;
- pull-request title;
- pull-request description;
- verified compare URL;
- release tag;
- release title;
- release notes.

## Clipboard behavior

Build application copies the pull-request description to the clipboard. Release
completion copies the release notes to the clipboard when GitHub CLI is
unavailable.

## Operator safeguards

The handoff file is stored under `handoff/` and may be used to recover any title
or description without searching through repository folders.
