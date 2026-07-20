from datetime import datetime, timezone
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path("src").resolve()))
from nrhis_harvest.texaset_et_harvest import TexasETObservation, build_regional_summary, render_markdown


def test_two_regions_are_summarized():
    rows = [
        TexasETObservation("Sinton", "coastal_bend", "2026-07-20T12:00:00Z", 0.24, 0.10, "https://texaset.tamu.edu"),
        TexasETObservation("Uvalde", "winter_garden", "2026-07-20T12:00:00Z", 0.31, 0.00, "https://texaset.tamu.edu"),
    ]
    result = build_regional_summary(rows, generated_at=datetime(2026, 7, 20, tzinfo=timezone.utc))
    assert result["regions"]["coastal_bend"]["mean_daily_eto_in"] == 0.24
    assert result["regions"]["winter_garden"]["station_count"] == 1
    assert "TexasET Regional Evapotranspiration" in render_markdown(result)


def test_negative_values_are_rejected():
    try:
        TexasETObservation.from_mapping({"station":"X","region":"coastal_bend","observed_at":"2026-07-20T00:00:00Z","eto_in":-1,"source_url":"x"})
    except ValueError:
        return
    raise AssertionError("negative ETo should be rejected")


def test_registry_contains_requested_regions():
    cfg = json.loads(Path("config/nrhis/texaset_regions.json").read_text(encoding="utf-8"))
    assert "coastal_bend" in cfg["regions"]
    assert "winter_garden" in cfg["regions"]
    assert any(x["name"] == "Sinton" for x in cfg["regions"]["coastal_bend"]["stations"])
    assert any(x["name"] == "Uvalde" for x in cfg["regions"]["winter_garden"]["stations"])
