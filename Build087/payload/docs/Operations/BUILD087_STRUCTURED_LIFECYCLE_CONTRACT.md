# Build087 Structured Release-Lifecycle Contract

Build087 centralizes the verified release-lifecycle requirements in a machine-readable JSON contract. A Python validator checks the operational lifecycle script against named capabilities and writes a validation receipt.

This does not weaken the existing CI, merge, completion, archive, or resume gates. It makes contract drift visible in one place and allows future tests to assert capabilities rather than scattering undocumented literal requirements across build-specific tests.

Validation command:

```powershell
python .\scripts\release\validate_release_lifecycle_contract.py
```

Receipt:

```text
data\nrhis\release\lifecycle-contract-validation.json
```
