# NRHIS Sprint 2 Build097 Release Notes

Build097 begins the analytical phase of NRHIS. It adds a local-only Rincon Bayou evidence workflow that automatically identifies material discharge gaps, measures whether stage monitoring continued during those gaps, detects the terminal published discharge observation, and summarizes contiguous negative-flow intervals.

Every run is bound by SHA-256 to the finalized historical CSV, the sparse query index, and its generated evidence tables. The workflow makes zero USGS requests and does not modify the finalized archive.
