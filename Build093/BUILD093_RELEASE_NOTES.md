# NRHIS Sprint 2 Build093 Release Notes

Build093 fixes the post-merge installer-archive guard in the self-contained release lifecycle. Each `Test-Path` call is now independently parenthesized, preventing the `PathType` parameter from being bound twice while preserving automatic installer evidence packaging and closeout.
