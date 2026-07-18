# ES-013 Sprint Archive Control

ES-013 defines the immutable archive used to preserve the accepted Sprint release inventory and closeout report.

Every Sprint archive contains `release_inventory.json`, `sprint_closeout.json`, `sprint_archive_manifest.json`, and SHA-256 and byte-size records for each archived artifact.

An archive may be created only from a closeout report whose `accepted` value is true. Existing archive identifiers are never overwritten. Validation fails when an artifact is missing, its byte size changes, its SHA-256 changes, or the archive contains a different artifact set.

Sprint archiving is additive and does not modify source records or the preserved legacy Pass1 tree.
