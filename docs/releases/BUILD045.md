# NRHIS Sprint 2 Build045

Build045 adds automatic CI-failure diagnostics and same-command lifecycle recovery. When a pull request remains blocked after the merge wait window, the lifecycle writes external text and JSON evidence for the checks and recent workflow runs, opens the pull request, and exits safely. Rerunning the same one-step command resumes from the existing branch and pull request without rebuilding.
