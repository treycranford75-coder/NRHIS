from __future__ import annotations

from datetime import datetime, timedelta, timezone
import random

from nrhis_analysis.lower_nueces_flow_transition_contrast import (
    _find_upper_flow_transition,
    _flow_band_scan,
    _split_threshold_scan,
)


def _synthetic_transition_series() -> tuple[dict, dict]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    upstream = {}
    downstream = {}
    rng_upstream = random.Random(12345)
    rng_noise = random.Random(54321)
    for i in range(1000):
        hour = start + timedelta(hours=i)
        value = rng_upstream.uniform(0.0, 100.0)
        upstream[hour] = value
        if value >= 70:
            downstream_value = value + rng_noise.uniform(-0.2, 0.2)
        else:
            downstream_value = rng_noise.uniform(0.0, 100.0)
        downstream[hour + timedelta(hours=4)] = downstream_value
    return upstream, downstream


def test_split_transition_identifies_upper_flow_contrast_near_70th_percentile() -> None:
    upstream, downstream = _synthetic_transition_series()
    rows = _split_threshold_scan(
        upstream,
        downstream,
        pair="synthetic",
        max_lag_hours=12,
        min_paired_hours=48,
        percentile_step=5,
        min_transition_percentile=60,
        max_transition_percentile=90,
        coherence_r=0.8,
        strong_r=0.9,
    )
    transition = _find_upper_flow_transition(
        rows,
        coherence_r=0.8,
        max_lower_r=0.5,
        confirm_steps=2,
    )
    assert transition is not None
    assert transition["threshold_percentile"] == 70
    assert transition["upper_best_lag_hours"] == 4
    assert float(transition["upper_best_pearson_r"]) > 0.8
    assert float(transition["lower_best_pearson_r"]) < 0.5


def test_transition_not_reported_when_lower_and_upper_subsets_are_both_coherent() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    upstream = {
        start + timedelta(hours=i): float((i * 17) % 101 + i / 1000.0)
        for i in range(1000)
    }
    downstream = {
        hour + timedelta(hours=5): value
        for hour, value in upstream.items()
    }
    rows = _split_threshold_scan(
        upstream,
        downstream,
        pair="synthetic",
        max_lag_hours=12,
        min_paired_hours=48,
        percentile_step=5,
        min_transition_percentile=60,
        max_transition_percentile=90,
        coherence_r=0.8,
        strong_r=0.9,
    )
    transition = _find_upper_flow_transition(
        rows,
        coherence_r=0.8,
        max_lower_r=0.5,
        confirm_steps=2,
    )
    assert transition is None


def test_nonoverlapping_flow_bands_do_not_leak_high_flow_signal_downward() -> None:
    upstream, downstream = _synthetic_transition_series()
    rows = _flow_band_scan(
        upstream,
        downstream,
        pair="synthetic",
        max_lag_hours=12,
        min_paired_hours=48,
        band_width_percentile=20,
        coherence_r=0.8,
        strong_r=0.9,
    )
    low = next(row for row in rows if row["band_percentile_low"] == 0)
    top = next(row for row in rows if row["band_percentile_low"] == 80)
    assert float(low["best_pearson_r"]) < 0.5
    assert top["best_lag_hours"] == 4
    assert float(top["best_pearson_r"]) > 0.99


def test_transition_confirmation_rejects_single_step_spike() -> None:
    rows = [
        {
            "threshold_percentile": 60,
            "lower_best_pearson_r": 0.2,
            "upper_best_pearson_r": 0.85,
            "upper_boundary_lag": False,
        },
        {
            "threshold_percentile": 65,
            "lower_best_pearson_r": 0.2,
            "upper_best_pearson_r": 0.4,
            "upper_boundary_lag": False,
        },
    ]
    transition = _find_upper_flow_transition(
        rows,
        coherence_r=0.8,
        max_lower_r=0.5,
        confirm_steps=2,
    )
    assert transition is None
