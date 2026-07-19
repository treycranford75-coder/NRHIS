NRHIS Sprint 2 Build039 — Safe Build Chaining

From the NRHIS repository root run:

  .\scripts\release\Start-NrhisBuild.ps1 -BuildNumber "039"

Build039 runs the established one-step lifecycle. After Build039 is merged, published, and verified, it looks for Build040's root ZIP and SHA-256 file and starts Build040 automatically. If Build040 is not present, it stops cleanly and reports that it is waiting.

To disable chaining when invoking the Build039 entry point directly:

  .\Build039\Complete-Build039.ps1 -NoChain

Permanent safeguards remain: develop merge target, no-prune synchronization, syntax/test gates, payload-authoritative reruns, complete staging, legacy preservation, pre-release publication, authenticated verification, and external completion evidence.
