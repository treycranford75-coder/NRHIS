# ES-017 Sprint Archive Retention Action Manifest

ES-017 defines a controlled action manifest derived from an approved archive
retention plan.

The manifest records the exact plan SHA-256, approval SHA-256, dry-run status,
action count, archive identifier, requested action, and reason.

Generation and validation are non-destructive. Build021 does not delete, move,
or quarantine archive files. It creates a reviewable action manifest only.
