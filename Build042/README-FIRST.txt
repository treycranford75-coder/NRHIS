NRHIS Sprint 2 Build042

Leave the ZIP and .sha256 file in Downloads or place them in the NRHIS repository root.
Run from the NRHIS repository root:

.\scripts\release\Start-NrhisBuild.ps1 -BuildNumber "042"

Build042 preserves the proven one-step lifecycle and removes the recurring Git for Windows prompt:

Deletion of directory '...' failed. Should I try again? (y/n)

The lifecycle now supplies "n" noninteractively, logs Git's output, preserves tracked and legacy artifacts, retains no-prune synchronization, and continues unless a required Git operation actually fails after its normal retry.
