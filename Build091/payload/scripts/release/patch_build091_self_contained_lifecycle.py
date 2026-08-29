from __future__ import annotations

from pathlib import Path


def main() -> int:
    repo = Path.cwd()
    target = repo / "scripts" / "release" / "Invoke-NrhisSelfContainedBuild.ps1"
    if not target.is_file():
        raise SystemExit(f"Missing target lifecycle helper: {target}")

    text = target.read_text(encoding="utf-8")

    anchor = '''if ($currentBranch -ne $branch) {\n    throw "Expected branch '$branch' but found '$currentBranch'. The wrapper must prepare the branch before invoking the runner."\n}\n$temporaryNotes = Join-Path $env:TEMP "NRHIS-Build$BuildNumber-release-notes.md"\n'''

    replacement = '''if ($currentBranch -ne $branch) {\n    throw "Expected branch '$branch' but found '$currentBranch'. The wrapper must prepare the branch before invoking the runner."\n}\n\n$completionGenerator = Join-Path $repo 'scripts/release/New-NrhisCompletionWrapper.ps1'\nif (-not (Test-Path $completionGenerator -PathType Leaf)) {\n    throw "Completion-wrapper generator not found: $completionGenerator"\n}\n\n& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $completionGenerator `\n    -BuildNumber $BuildNumber `\n    -RepositoryRoot $repo `\n    -Tag $ReleaseTag `\n    -ReleaseTitle $ReleaseTitle `\n    -NotesFile $ReleaseNotesFile\nif ($LASTEXITCODE -ne 0) {\n    throw "Build$BuildNumber completion-wrapper generation failed."\n}\n\n$wrapperRelativePath = "Build$BuildNumber/Complete-Build$BuildNumber.ps1"\n$wrapperPath = Join-Path $repo $wrapperRelativePath\nif (-not (Test-Path $wrapperPath -PathType Leaf)) {\n    throw "Build$BuildNumber completion wrapper was not generated: $wrapperPath"\n}\n$StagedPaths = @($StagedPaths) + $wrapperRelativePath\n$StagedPaths = @($StagedPaths | Select-Object -Unique)\n\n$temporaryNotes = Join-Path $env:TEMP "NRHIS-Build$BuildNumber-release-notes.md"\n'''

    if "New-NrhisCompletionWrapper.ps1" not in text:
        if anchor in text:
            text = text.replace(anchor, replacement, 1)
        else:
            marker = '$temporaryNotes = Join-Path $env:TEMP "NRHIS-Build$BuildNumber-release-notes.md"\n'
            if marker not in text:
                raise SystemExit("Unable to locate lifecycle insertion anchor or fallback marker.")
            insertion = "\n" + replacement[replacement.index("$completionGenerator"):]
            text = text.replace(marker, insertion, 1)

    expected_add = "Invoke-Native git (@('add', '--') + $StagedPaths) | Out-Null"
    if expected_add not in text:
        raise SystemExit("Unable to locate canonical explicit git staging allowlist.")

    expected_receipt = "        staged_paths = $StagedPaths"
    if expected_receipt not in text:
        raise SystemExit("Unable to locate canonical staged_paths receipt field.")

    target.write_text(text, encoding="utf-8", newline="\n")
    print(f"Build091 patched {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
