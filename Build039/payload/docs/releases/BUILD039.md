# NRHIS Sprint 2 Build039

Build039 adds safe chain-to-next-build execution after verified completion.

## Controls

- Chains only after a valid `status: verified` completion receipt exists.
- Calculates exactly the next sequential three-digit build number.
- Never skips a build.
- Requires the next one-step ZIP and its `.sha256` companion.
- Validates SHA-256 before starting the next build.
- Searches the repository root, repository parent, and the user Downloads folder.
- Stops cleanly when the next ZIP is not present.
- Enforces a 25-build recursion safety limit.
- Supports `-NoChain` to disable automatic advancement.
- Retains all Build038 lifecycle and release-verification controls.
