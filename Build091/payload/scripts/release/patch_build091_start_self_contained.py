from __future__ import annotations

from pathlib import Path


def main() -> int:
    repo = Path.cwd()
    target = repo / "scripts" / "release" / "Start-NrhisBuild.ps1"
    if not target.is_file():
        raise SystemExit(f"Missing starter: {target}")

    text = target.read_text(encoding="utf-8")
    anchor = '''& powershell.exe @childArguments\nif ($LASTEXITCODE -ne 0) { throw "Build$BuildNumber child process failed with exit code $LASTEXITCODE." }\nif ($SkipPullRequest) {\n'''
    replacement = '''& powershell.exe @childArguments\nif ($LASTEXITCODE -ne 0) { throw "Build$BuildNumber child process failed with exit code $LASTEXITCODE." }\n\n# A self-contained build may have already completed PR, merge, release, receipts, and cleanup.\n$closureReceipt = Join-Path $HOME "NRHIS-Release-Evidence\\Build$BuildNumber\\completion-closure-receipt.json"\nif (Test-Path $closureReceipt -PathType Leaf) {\n    $branchAfterChild = (@(& git branch --show-current) -join "`n").Trim()\n    if ($LASTEXITCODE -eq 0 -and $branchAfterChild -eq 'develop') {\n        Write-Host "Build$BuildNumber self-contained lifecycle already completed; legacy outer lifecycle skipped." -ForegroundColor Green\n        exit 0\n    }\n}\n\nif ($SkipPullRequest) {\n'''

    if "self-contained lifecycle already completed; legacy outer lifecycle skipped" not in text:
        if anchor in text:
            text = text.replace(anchor, replacement, 1)
        else:
            marker = 'if ($SkipPullRequest) {\n'
            if marker not in text:
                raise SystemExit("Unable to locate starter post-child anchor or fallback marker.")
            insertion = replacement[replacement.index("# A self-contained build"):]
            text = text.replace(marker, insertion, 1)

    target.write_text(text, encoding="utf-8", newline="\n")
    print(f"Build091 patched {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
