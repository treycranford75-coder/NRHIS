# NRHIS Sprint 2 Build038

Build038 removes the final private-repository verification workaround from the
one-ZIP lifecycle. Every GitHub REST request now uses the authenticated GitHub
CLI token when available, including release lookup, tag-reference resolution,
and annotated-tag dereferencing.

Commit values are normalized before authoritative full-SHA comparison. The
workflow remains resumable and fail-closed.
