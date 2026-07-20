# Build078 Release Notes

Build078 fixes the completion-to-archive contract exposed during Build077. New completion receipts are immediately accepted by the installer archival gate, and first-time prerelease publication no longer fails when `gh release view` reports that the release does not yet exist.
