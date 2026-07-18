# Calibration Reference Catalog Runbook

## List all cases

```powershell
python -m nrhis_calibration.reference_catalog_cli `
  .\data\calibration-reference-cases
```

## List approved and valid cases

```powershell
python -m nrhis_calibration.reference_catalog_cli `
  .\data\calibration-reference-cases `
  --approved-only `
  --valid-only
```

## Filter by implementation

```powershell
python -m nrhis_calibration.reference_catalog_cli `
  .\data\calibration-reference-cases `
  --implementation legacy-pass1
```

## Export JSON

```powershell
python -m nrhis_calibration.reference_catalog_cli `
  .\data\calibration-reference-cases `
  --json-output .\reports\calibration-reference-catalog.json
```

Invalid cases remain visible with their validation errors.
