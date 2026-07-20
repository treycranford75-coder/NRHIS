# Build086 CI Registration Retry

Build086 distinguishes a pull request with failed checks from a pull request whose checks have not yet registered with GitHub.

The release lifecycle now retries the `no checks reported` state for up to 120 seconds. During that window the lifecycle remains pending and does not report a false CI failure. If checks register, normal watch and fail-fast behavior begins. Genuine failed checks still block automatic merge and preserve the resume command.
