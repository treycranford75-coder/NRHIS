# NRHIS Sprint 2 Build062 — Twice-Daily Operations Cycle Runner

Build062 turns the individual NRHIS harvest and publication commands into one auditable operational cycle. The runner executes each required source and calculation stage in order, preserves a log for every stage, blocks downstream publication after a required failure, and writes machine-readable cycle evidence.

Publication is authorized only when the full cycle completes and both mandatory verification passes are recorded.
