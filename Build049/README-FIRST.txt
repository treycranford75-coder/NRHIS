NRHIS Sprint 2 Build049

Run from the current NRHIS repository root:

  .\scripts\release\Start-NrhisBuild.ps1 -BuildNumber "049"

If the repository is inside OneDrive, Build049 will create or update a protected clone at C:\GitHub\NRHIS, copy the verified Build049 ZIP and checksum there, write a migration receipt, and continue the same lifecycle from the non-synced repository.

Build049 never prunes branches or remote references. It fails closed if the destination is unsafe or migration validation fails.
