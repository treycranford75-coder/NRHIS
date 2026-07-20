## NRHIS Sprint 2 — Build068

Build068 adds real scheduler freshness and missed-run detection.

### Included
- validates `completed_at` on the canonical scheduler receipt;
- flags stale receipts using `receipt_max_age_hours`;
- flags missed Morning or Evening slots after `grace_minutes`;
- preserves the Build066 config contract and expected slot names;
- adds deterministic tests for healthy, stale, and missed-run cases.
