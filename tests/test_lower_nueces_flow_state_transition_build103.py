from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import random

from nrhis_analysis.lower_nueces_flow_state_transition import (
    _detect_high_flow_events,
    _find_sustained_coherence_onset,
    _lag_surface_for_hours,
    _threshold_scan,
)
from nrhis_analysis.lower_nueces_lag_stability import _best_and_peak_windows


def test_threshold_scan_separates_weak_full_series_from_high_flow_coherence() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    upstream = {}
    downstream = {}
    rng_upstream = random.Random(12345)
    rng_noise = random.Random(54321)
    for i in range(600):
        hour = start + timedelta(hours=i)
        value = rng_upstream.uniform(0.0, 100.0)
        upstream[hour] = value
        if value >= 70:
            downstream[hour + timedelta(hours=4)] = value
        else:
            downstream[hour + timedelta(hours=4)] = rng_noise.uniform(0.0, 100.0)
    rows = _threshold_scan(
        upstream,
        downstream,
        pair="synthetic",
        max_lag_hours=12,
        min_paired_hours=48,
        percentile_step=10,
        coherence_r=0.8,
        strong_r=0.9,
    )
    assert float(rows[0]["best_pearson_r"]) < 0.8
    assert float(rows[-1]["best_pearson_r"]) > 0.99
    assert rows[-1]["best_lag_hours"] == 4


def test_sustained_onset_requires_confirming_thresholds() -> None:
    rows = [
        {
            "threshold_percentile": 50,
            "threshold_cfs": 70.0,
            "best_lag_hours": 4,
            "best_pearson_r": 0.81,
            "best_paired_hours": 100,
            "boundary_lag": False,
        },
        {
            "threshold_percentile": 55,
            "threshold_cfs": 75.0,
            "best_lag_hours": 4,
            "best_pearson_r": 0.84,
            "best_paired_hours": 90,
            "boundary_lag": False,
        },
        {
            "threshold_percentile": 60,
            "threshold_cfs": 80.0,
            "best_lag_hours": 4,
            "best_pearson_r": 0.88,
            "best_paired_hours": 80,
            "boundary_lag": False,
        },
    ]
    onset = _find_sustained_coherence_onset(rows, coherence_r=0.8, confirm_steps=3)
    assert onset is not None
    assert onset["threshold_percentile"] == 50
    assert onset["confirmed_through_percentile"] == 60


def test_event_detection_merges_small_gaps() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    values = {
        start + timedelta(hours=i): 100.0
        for i in list(range(0, 6)) + list(range(8, 15))
    }
    events = _detect_high_flow_events(
        values,
        threshold=90.0,
        gap_tolerance_hours=2,
        min_high_hours=10,
    )
    assert len(events) == 1
    assert events[0]["high_hours"] == 13


def test_event_lag_surface_recovers_known_shift() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    upstream = {
        start + timedelta(hours=i): float((i * 11) % 47 + i / 10)
        for i in range(80)
    }
    downstream = {
        hour + timedelta(hours=5): value
        for hour, value in upstream.items()
    }
    hours = list(upstream)
    surface = _lag_surface_for_hours(
        upstream,
        downstream,
        hours,
        max_lag_hours=12,
        min_paired_hours=20,
    )
    peak = _best_and_peak_windows(surface)
    assert peak["best_lag_hours"] == 5
    assert peak["best_pearson_r"] == 1.0



def test_full_analysis_writes_outputs_from_local_hourly_data(
    tmp_path, monkeypatch
) -> None:
    import nrhis_analysis.lower_nueces_flow_state_transition as mod

    csv_path = tmp_path / "history.csv"
    index_path = tmp_path / "index.json"
    csv_path.write_text("placeholder\n", encoding="utf-8")
    index_path.write_text("{}\n", encoding="utf-8")

    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    mathis = {
        start + timedelta(hours=i):
            float(20 + ((i * 17) % 83) + i / 1000)
        for i in range(220)
    }

    bluntzer = {
        hour + timedelta(hours=2): value
        for hour, value in mathis.items()
    }

    calallen = {
        hour + timedelta(hours=4): value
        for hour, value in mathis.items()
    }

    hourly = {
        "08211000": mathis,
        "08211200": bluntzer,
        "08211500": calallen,
    }

    coverage = {
        site: {
            "raw_discharge_records": len(values),
            "valid_discharge_records": len(values),
            "hourly_bins_retained": len(values),
            "hourly_bins_excluded_low_count": 0,
        }
        for site, values in hourly.items()
    }

    monkeypatch.setattr(
        mod,
        "load_sparse_index",
        lambda index, csv: {
            "source_csv_bytes": csv_path.stat().st_size,
            "source_csv_sha256": mod.sha256_file(csv_path),
        },
    )

    monkeypatch.setattr(
        mod,
        "normalize_window",
        lambda start_value, end_value: (
            "2026-01-01T00:00:00Z",
            "2026-01-10T00:00:00Z",
        ),
    )

    monkeypatch.setattr(
        mod,
        "query_history",
        lambda *args, **kwargs: [],
    )

    monkeypatch.setattr(
        mod,
        "_build_hourly_values",
        lambda *args, **kwargs: (hourly, coverage),
    )

    output_dir = tmp_path / "analysis"

    summary = mod.analyze_lower_nueces_flow_state_transition(
        csv_path,
        index_path,
        output_dir,
        start="2026-01-01",
        end="2026-01-10",
        max_lag_hours=8,
        min_paired_hours=20,
        percentile_step=25,
        confirm_steps=2,
        event_gap_tolerance_hours=0,
        min_event_high_hours=10,
        event_min_paired_hours=10,
    )

    assert summary["network_requests_made"] == 0
    assert summary["threshold_scan_row_count"] > 0
    assert summary["tercile_regime_row_count"] == 9
    assert summary["coherent_flow_event_row_count"] >= 3
    assert summary["coherent_flow_residual_row_count"] == 3

    assert Path(summary["receipt"]).is_file()

    assert (output_dir / "coherence_threshold_scan.csv").is_file()
    assert (output_dir / "coherence_onset.csv").is_file()
    assert (output_dir / "tercile_regime_coherence.csv").is_file()
    assert (output_dir / "coherent_flow_event_lags.csv").is_file()
    assert (output_dir / "coherent_flow_residual_summary.csv").is_file()
    assert (
        output_dir / "lower_nueces_flow_state_transition_summary.json"
    ).is_file()
