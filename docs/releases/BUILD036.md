# Sprint 2 Build036 — Automated Pre-Release Publication and Verification Closure

Build036 reduces the post-merge release lifecycle to one completion command.

## Added
- Automatic no-prune synchronization of `develop`.
- GitHub CLI authentication detection.
- Automatic pre-release publication targeting the exact merged commit.
- Optional upload of the original one-step ZIP as a release asset.
- Automatic public release retrieval and exact tag-reference resolution.
- Normalized external verification JSON with a resolved commit SHA.
- Automatic invocation of verification closure, evidence indexing, and receipt validation.
- Browser fallback that resumes automatically when the same command is rerun.

## Corrected
- Verification values are trimmed before tag and commit comparison, preventing invisible whitespace from producing a false mismatch.

## Preserved
- `develop` merge target.
- No-prune synchronization.
- PowerShell parser gate before Python validation.
- Ruff, full pytest, branch coverage at or above 80%, and whitespace checks.
- Payload-authoritative installation and complete staging.
- Pre-release publication, never latest.
- External evidence storage.
- Legacy Pass1 preservation.
