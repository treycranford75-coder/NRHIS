# ES-012 Sprint Closeout Control

ES-012 defines the machine-readable closeout control for a completed NRHIS development sprint.

The closeout inventory records build number, release tag, merge commit, release title, passing test count, measured branch coverage, and pre-release status.

The closeout gate verifies uninterrupted build-number continuity, unique release tags, unique merge commits, coverage at or above the configured floor, positive test evidence, and pre-release classification for every release candidate.

Sprint closeout is accepted only when every required check passes.

Closeout evaluation is read-only and does not modify source code, release records, or the preserved legacy Pass1 tree.
