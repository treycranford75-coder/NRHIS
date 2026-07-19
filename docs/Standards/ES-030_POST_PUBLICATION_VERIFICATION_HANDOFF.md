# ES-030 Post-Publication Verification Handoff

## Purpose

ES-030 ensures every manually published NRHIS release is followed by the same
bounded verification used for automated publication.

## Manual publication path

After the release page opens, the workflow creates an external verification
handoff containing:

- exact tag;
- exact release title;
- exact release-notes file;
- bounded verification command;
- expected evidence path.

The verification command is copied to the clipboard.

## Automated publication path

When GitHub CLI is authenticated, release completion publishes the pre-release
and immediately waits for public verification before reporting success.
