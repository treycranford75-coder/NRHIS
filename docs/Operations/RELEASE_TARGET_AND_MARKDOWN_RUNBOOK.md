# Release Target and Markdown Safety Runbook

## Pull-request verification

Before creating a pull request, confirm:

- base branch is `develop`;
- compare branch is the intended feature branch;
- commit count matches the build;
- file count matches the build payload.

## Manual release publication

When GitHub CLI is unavailable, the completion script copies Markdown release
notes to the clipboard and opens a release page prefilled with the correct tag
and title.

Paste the clipboard contents directly into the GitHub release-notes field.
