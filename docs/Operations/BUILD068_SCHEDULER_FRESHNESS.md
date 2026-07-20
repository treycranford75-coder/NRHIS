# Build068 Scheduler Freshness and Missed-Run Detection

Build068 extends scheduler health monitoring with actual receipt-age validation and missed-slot detection. A scheduler receipt can now be present and still be classified as unhealthy when it is stale or when a scheduled morning/evening run was missed beyond the configured grace period.

Problem codes include `stale_scheduler_run_receipt`, `invalid_scheduler_completed_at`, and `missed_schedule_slot:<name>`.
