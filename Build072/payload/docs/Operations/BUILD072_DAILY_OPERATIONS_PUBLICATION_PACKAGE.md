# Build072 — Daily Operations Publication Package

Build072 converts the verified Build070 daily operations report into an immutable, dated publication package. Each package contains the JSON, Markdown, and print-ready HTML report plus a checksum manifest. The publisher also updates a latest-package pointer, appends package history, and writes an operational completion receipt.

The default release gate blocks packaging unless the report QA status is passed, approved, released, publication-ready, or complete. `-AllowUnreleased` is reserved for explicit diagnostics and labels the manifest `unreleased_override`.
