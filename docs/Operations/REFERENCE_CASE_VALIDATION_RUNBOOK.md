# Reference-Case Validation Runbook

## Validate a development case

```powershell
python -m nrhis_calibration.reference_cli path\to\case.json
```

## Require approval

```powershell
python -m nrhis_calibration.reference_cli path\to\case.json --require-approved
```

The command verifies every artifact path and SHA-256 digest.

## Failure conditions

- malformed manifest
- missing required field
- missing artifact
- SHA-256 mismatch
- negative tolerance
- unapproved case when approval is required

## Preservation

Reference cases are additive and must not modify the preserved legacy Pass1
tree.
