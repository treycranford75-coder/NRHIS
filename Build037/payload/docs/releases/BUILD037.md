# NRHIS Sprint 2 Build037

Build037 consolidates the complete build lifecycle behind the original one-step root ZIP.

The same safe-to-rerun command now advances the build through every state it can automate:

1. synchronize `develop` without pruning;
2. create or resume the feature branch;
3. apply the ZIP payload authoritatively;
4. run PowerShell, Ruff, pytest/branch-coverage, and whitespace gates;
5. stage, commit, and push the complete build;
6. create the pull request against `develop` through GitHub CLI;
7. enable auto-merge and wait for required checks when repository policy permits;
8. synchronize the merged `develop` branch;
9. publish the exact-commit GitHub pre-release;
10. resolve the release tag to its authoritative commit;
11. create normalized external evidence and update the evidence index;
12. close verification and confirm the completion receipt.

Browser pages are used only when GitHub CLI cannot be installed, authenticated, or authorized for a required action. Rerunning the same command resumes from the last completed checkpoint.
