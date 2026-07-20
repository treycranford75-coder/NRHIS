# Build081 Automatic Pull-Request Resolution

Build081 removes the need to copy a pull-request URL from the terminal. When the lifecycle receives a blank or known placeholder value, it resolves the pull request from `feature/sprint2-buildNNN` using GitHub CLI and validates the resulting URL before continuing.
