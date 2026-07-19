NRHIS Sprint 2 Build041

Leave the ZIP and .sha256 file in Downloads or place them in the NRHIS repository root.
Run from the NRHIS repository root:

.\scripts\release\Start-NrhisBuild.ps1 -BuildNumber "041"

Build041 preserves the proven one-step lifecycle and adds verified post-completion archival of installer artifacts. The archive and its SHA-256 manifest are written outside the repository under NRHIS-Release-Evidence. Git-tracked and legacy files are preserved; only known untracked transient extraction remnants may be removed.

Optional opt-out for archival:

.\Build041\Apply-Build041.ps1 -NoArchive
