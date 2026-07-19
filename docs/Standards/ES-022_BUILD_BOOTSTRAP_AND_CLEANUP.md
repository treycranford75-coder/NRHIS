# ES-022 Build Bootstrap and Cleanup

## Purpose

ES-022 defines a permanent one-command NRHIS build bootstrap and automatic
cleanup of temporary starter scripts.

## Bootstrap behavior

The generic starter:

- accepts a three-digit build number;
- locates the matching one-step ZIP in the repository root, Downloads,
  OneDrive Downloads, or Desktop;
- removes stale extraction folders;
- extracts the build;
- verifies the build-specific apply script;
- launches the apply script from the repository root.

## Cleanup behavior

Post-merge completion removes the build folder, one-step ZIP, and temporary
`Start-NRHIS-Build*.ps1` files before enforcing a clean working tree.

## Release URL safety

Manual release URLs must URL-encode both tag and title values.
