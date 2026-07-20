# Build088 Self-Contained One-Step Lifecycle

Build088 removes the build-completion dependency on branch-specific helper scripts. The new runner starts from the current remote base branch, validates the repository, creates or updates the feature branch, runs Ruff and pytest, opens the pull request, waits for registered CI checks, merges, publishes the prerelease, and writes completion receipts.

The companion package generator creates the next root ZIP and SHA-256 checksum locally, eliminating the requirement to upload an installer archive after every completed build.
