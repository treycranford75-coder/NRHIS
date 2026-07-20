# Build073 — Full One-Step Release Lifecycle

Build073 extends the one-step release workflow beyond pull-request creation. After the feature branch is pushed, the workflow creates or reuses the pull request, watches required CI checks, blocks on failure, merges into `develop`, updates the local base branch, runs the build completion script, archives installer artifacts, and emits the standard next-build prompt.

Manual stop points remain available through `-SkipPullRequest`, `-SkipLifecycle`, and `-SkipArchive` for deliberate diagnostics.
