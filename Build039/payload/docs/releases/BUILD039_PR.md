## NRHIS Sprint 2 — Build039

Build039 safely chains a verified build to the next sequential one-step root ZIP.

### Included

- Verified completion-receipt gate before chaining
- Exact sequential next-build calculation
- Next-ZIP discovery in approved locations
- Mandatory SHA-256 companion validation
- No skipped build numbers
- 25-build loop protection
- Clean waiting state when the next ZIP is unavailable
- `-NoChain` opt-out

### Permanent controls retained

- `develop` merge target
- No-prune synchronization
- PowerShell syntax gate
- Payload-authoritative reruns
- Complete staging
- Legacy preservation
- Automated pre-release publication
- Authenticated private-repository verification
- Post-publication evidence and completion receipt
