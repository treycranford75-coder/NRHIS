NRHIS Sprint 2 Build040

Place the ZIP and .sha256 file in Downloads or the NRHIS repository root.
Run from the NRHIS repository root:

.\scripts\release\Start-NrhisBuild.ps1 -BuildNumber "040"

Build040 adds expanded package discovery, automatic verified copying into the repository root, checksum-gated resumable extraction, whitespace-safe packaging, and noninteractive retry handling for transient Windows/OneDrive Git locks.
