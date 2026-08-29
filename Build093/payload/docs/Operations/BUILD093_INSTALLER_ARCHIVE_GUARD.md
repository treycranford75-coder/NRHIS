# Build093 - Installer Archive Lifecycle Guard

Build092 exposed a post-merge PowerShell parameter-binding defect in the self-contained lifecycle. The build itself passed local tests and CI, merged, and published its prerelease, but the lifecycle stopped while checking whether the build directory and packager existed.

The defective expression supplied `-PathType` twice to one syntactic command expression:

`if (Test-Path $buildDirectory -PathType Container -and Test-Path $packager -PathType Leaf) {`

Build093 makes the boolean expression explicit by parenthesizing each `Test-Path` invocation independently:

`if ((Test-Path $buildDirectory -PathType Container) -and (Test-Path $packager -PathType Leaf)) {`

This preserves the existing archive behavior while preventing `ParameterAlreadyBound` during post-merge closeout.

No production USGS historical requests are made by Build093. After Build093 closes, rerun `scripts/Bootstrap-USGS-History.ps1 -PlanOnly` and verify the eight-station network before starting the historical archive.
