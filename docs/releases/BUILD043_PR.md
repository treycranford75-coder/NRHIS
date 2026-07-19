## NRHIS Sprint 2 — Build043

Build043 permanently fixes native Git handling in the one-step lifecycle.

### Included

- Capture normal Git progress written to stderr without raising `NativeCommandError`
- Determine Git success only from the native exit code
- Preserve automatic `n` responses for locked-directory retry prompts
- Retain two-attempt transient Git retry behavior
- Preserve no-prune synchronization and all existing lifecycle gates

Build042 remains complete, published, verified, and archived.
