from datetime import date
from pathlib import Path

from nrhis_harvest import cli
from nrhis_harvest.models import HarvestResult


def test_cli_returns_zero_and_reports_outputs(monkeypatch, tmp_path: Path, capsys) -> None:
    def fake_harvest(*args, **kwargs):
        return HarvestResult(
            run_id="run",
            raw_path=tmp_path / "raw.json",
            normalized_path=tmp_path / "observations.csv",
            metadata_path=tmp_path / "metadata.json",
            station_count=1,
            observation_count=2,
        )

    monkeypatch.setattr(cli, "harvest_usgs", fake_harvest)
    code = cli.main(
        [
            "--registry",
            "config/stations/lower_nueces.yml",
            "--start",
            date(2026, 7, 17).isoformat(),
            "--end",
            date(2026, 7, 17).isoformat(),
        ]
    )
    assert code == 0
    assert "Observations: 2" in capsys.readouterr().out
