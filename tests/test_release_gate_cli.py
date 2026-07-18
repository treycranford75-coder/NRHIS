import sys
from pathlib import Path

import pytest

from nrhis_calibration import release_gate_cli
from nrhis_calibration.release_gate import ReleaseGateCheck, ReleaseGateReport


def test_release_gate_cli_returns_zero_for_acceptance(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = ReleaseGateReport(
        release_id="release-cli",
        accepted=True,
        evidence_manifest=str(tmp_path / "evidence_manifest.json"),
        checks=(
            ReleaseGateCheck(
                name="evidence_bundle_integrity",
                passed=True,
                detail="2 artifacts verified",
            ),
        ),
    )

    monkeypatch.setattr(
        release_gate_cli,
        "evaluate_release_gate",
        lambda **kwargs: report,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "release_gate_cli",
            "release-cli",
            "evidence_manifest.json",
            "--json-output",
            str(tmp_path / "release-gate.json"),
        ],
    )

    assert release_gate_cli.main() == 0
    output = capsys.readouterr().out
    assert "Accepted: True" in output
    assert "PASS evidence_bundle_integrity" in output
