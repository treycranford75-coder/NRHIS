NRHIS Sprint 2 Build036 — One-Step Root Package

PURPOSE
Build036 returns the release lifecycle to automation. The post-merge completion command now attempts to:
  1. synchronize develop without pruning;
  2. verify the merged commit;
  3. publish the GitHub pre-release with gh when authenticated;
  4. resolve the release tag to the exact commit SHA;
  5. generate normalized external verification evidence;
  6. close release verification and update the evidence index;
  7. verify completion-receipt.json exists and matches the build/tag/commit.

INSTALL / APPLY
From the NRHIS repository root run the permanent starter:

  .\scripts\release\Start-NrhisBuild.ps1 -BuildNumber "036"

Create and merge the PR:

  feature/sprint2-build036 -> develop

POST-MERGE ONE-STEP COMPLETION
After checks pass and the PR is merged:

  git switch develop
  .\Build036\Complete-Build036.ps1

The completion script performs its own no-prune fetch and fast-forward pull.

OPTIONAL RELEASE ASSET
To upload the original root ZIP as a release asset:

  .\Build036\Complete-Build036.ps1 -ReleaseAsset "$env:USERPROFILE\Downloads\NRHIS_Sprint2_Build036_OneStep.zip"

BROWSER FALLBACK
When GitHub CLI is missing or not authenticated, the script writes the publication handoff and opens the new-release page. After publishing in the browser, rerun the same completion command. It will detect the release and finish verification automatically.

Build036 remains a pre-release and must not be marked latest. Existing legacy Pass1 files are not modified.
