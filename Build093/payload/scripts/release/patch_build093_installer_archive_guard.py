from __future__ import annotations

from pathlib import Path

repo = Path.cwd()
runner = repo / "scripts" / "release" / "Invoke-NrhisSelfContainedBuild.ps1"
text = runner.read_text(encoding="utf-8")

old = "if (Test-Path $buildDirectory -PathType Container -and Test-Path $packager -PathType Leaf) {"
new = "if ((Test-Path $buildDirectory -PathType Container) -and (Test-Path $packager -PathType Leaf)) {"

if new in text:
    print(f"Build093 installer-archive guard already corrected: {runner}")
elif old in text:
    text = text.replace(old, new, 1)
    runner.write_text(text, encoding="utf-8", newline="\n")
    print(f"Patched: {runner}")
else:
    raise SystemExit("Unable to locate the Build092 installer-archive Test-Path guard.")
