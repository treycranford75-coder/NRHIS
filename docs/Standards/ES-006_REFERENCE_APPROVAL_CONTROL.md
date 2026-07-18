# ES-006 Calibration Reference Approval Control

## Purpose

ES-006 separates reference capture from reference approval and records the
reviewer, rationale, action, and timestamp for each approval decision.

## Approval prerequisites

A case may be approved only when:

- its manifest is valid;
- every listed artifact exists;
- every SHA-256 digest matches;
- the case is currently unapproved;
- the reviewer is identified;
- the rationale is non-empty;
- no prior approval record exists.

## Approval result

Approval creates `approval_record.json` and changes the manifest approval state
to true.

## Revocation

Approval may be revoked without deleting the original approval record.
Revocation creates `revocation_record.json`, records the reviewer and rationale,
and changes the manifest approval state to false.

## Separation of duties

Capture and approval are separate actions. Build009 capture always creates
unapproved cases. Build010 approval requires an explicit reviewer and rationale.

## Preservation

Approval controls are additive and do not modify the preserved legacy Pass1
tree.
