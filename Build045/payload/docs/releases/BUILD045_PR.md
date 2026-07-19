## NRHIS Sprint 2 — Build045

Build045 improves failure visibility and recovery when required GitHub checks block automated merging.

### Included

- Capture pull-request check output after the merge wait window
- Capture recent GitHub Actions run status, conclusion, URL, event, and commit
- Store CI diagnostics outside the repository under the Build045 evidence directory
- Open the blocked pull request automatically for review
- Resume safely from the same one-step command after a CI repair or manual merge
- Preserve behavior-based workflow tests and all established release gates

Build044 remains complete, published, verified, and archived.
