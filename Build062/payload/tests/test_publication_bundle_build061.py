from __future__ import annotations

from datetime import datetime, timezone

from nrhis_harvest.publication_bundle import build_bundle, evaluate_gate, flatten_public_rows


def _snapshot(status: str = "ready") -> dict:
    return {
        "overall_status": status,
        "river": {"stations": [{"station_id": "08211500", "discharge_cfs": 10.0}]},
        "forecast": {"category": "below_action"},
        "reservoirs": {"reservoirs": [{"reservoir_id": "lake-corpus-christi", "percent_full": 50.0}]},
        "coastal": {"station_id": "SALT03", "salinity_ppt": 12.5},
    }


def test_ready_snapshot_requires_two_qa_passes() -> None:
    gate = evaluate_gate(_snapshot(), required_sections=["river", "forecast", "reservoirs", "coastal"], qa_passes_completed=1)
    assert gate.status == "not_ready"
    assert gate.publish_allowed is False
    assert "QA incomplete" in gate.reasons[0]


def test_ready_snapshot_is_authorized_after_two_passes() -> None:
    bundle = build_bundle(
        _snapshot(),
        qa_passes_completed=2,
        required_sections=["river", "forecast", "reservoirs", "coastal"],
        generated_at=datetime(2026, 7, 20, tzinfo=timezone.utc),
    )
    assert bundle["publish_allowed"] is True
    assert bundle["publication_status"] == "ready"
    assert bundle["qa"]["post_generation_visual_qa_required"] is True


def test_missing_section_blocks_publication() -> None:
    snapshot = _snapshot()
    snapshot.pop("coastal")
    gate = evaluate_gate(snapshot, required_sections=["river", "forecast", "reservoirs", "coastal"], qa_passes_completed=2)
    assert gate.publish_allowed is False
    assert "missing required section: coastal" in gate.reasons


def test_public_rows_include_river_reservoir_and_coastal() -> None:
    rows = flatten_public_rows(_snapshot())
    assert {row["section"] for row in rows} == {"river", "reservoir", "coastal"}
