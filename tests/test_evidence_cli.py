import sys
from pathlib import Path

import pytest

from nrhis_calibration import evidence_cli


def test_evidence_cli_create_and_validate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    artifact = tmp_path / "summary.json"
    artifact.write_text('{"matched": true}\n', encoding="utf-8")
    destination_root = tmp_path / "evidence"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "evidence_cli",
            "create",
            str(destination_root),
            "bundle-1",
            str(artifact),
            "--metadata-json",
            '{"release": "rc14"}',
        ],
    )
    assert evidence_cli.main() == 0
    create_output = capsys.readouterr().out
    assert "Artifacts: 1" in create_output

    manifest = destination_root / "bundle-1" / "evidence_manifest.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["evidence_cli", "validate", str(manifest)],
    )
    assert evidence_cli.main() == 0
    validate_output = capsys.readouterr().out
    assert "Verified artifacts: 1" in validate_output
