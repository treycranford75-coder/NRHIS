# Build091 - Durable Completion Wrapper Contract

Build091 closes the release gap exposed by Build090, where a build could merge successfully but the resumable lifecycle could not finish because `BuildNNN/Complete-BuildNNN.ps1` was absent.

## Permanent contract

Every build using `Invoke-NrhisSelfContainedBuild.ps1` now creates and stages a build-specific completion wrapper before commit and push.

The generated wrapper:

- accepts `-RepositoryRoot`;
- delegates publication and verified receipt creation to `scripts/release/Complete-NrhisBuild.ps1`;
- carries the build number, release tag, release title, and notes path supplied by the build;
- is PowerShell-syntax validated when generated;
- is committed inside `BuildNNN`, so `Finish-NrhisBuildLifecycle.ps1` can find it after merge or during a resumed closeout.

Build091 also updates `Start-NrhisBuild.ps1` so a future self-contained build that already completed its merge/release/receipt/cleanup lifecycle is not sent through the legacy outer PR/lifecycle path a second time.
