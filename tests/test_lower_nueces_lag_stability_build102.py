from __future__ import annotations

from datetime import datetime, timedelta, timezone

from nrhis_analysis.lower_nueces_lag_stability import (
    _best_and_peak_windows,
    _lag_surface,
    _overlap,
)


def test_best_lag_recovers_known_three_hour_shift() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    upstream = {start + timedelta(hours=i): float((i * 7) % 31 + i / 10) for i in range(240)}
    downstream = {hour + timedelta(hours=3): value for hour, value in upstream.items()}
    surface = _lag_surface(upstream, downstream, max_lag_hours=12, min_paired_hours=48)
    peak = _best_and_peak_windows(surface)
    assert peak["best_lag_hours"] == 3
    assert peak["best_pearson_r"] == 1.0


def test_peak_window_retains_near_optimal_lags() -> None:
    surface = [
        {"lag_hours": 16, "paired_hours": 100, "pearson_r": 0.9879},
        {"lag_hours": 17, "paired_hours": 100, "pearson_r": 0.98816},
        {"lag_hours": 18, "paired_hours": 100, "pearson_r": 0.98822},
        {"lag_hours": 19, "paired_hours": 100, "pearson_r": 0.98800},
        {"lag_hours": 20, "paired_hours": 100, "pearson_r": 0.98750},
    ]
    peak = _best_and_peak_windows(surface)
    assert peak["best_lag_hours"] == 18
    assert peak["lag_min_delta0005"] == 16
    assert peak["lag_max_delta0005"] == 19
    assert peak["lag_min_delta001"] == 16
    assert peak["lag_max_delta001"] == 20


def test_additive_window_overlap_helper() -> None:
    overlap = _overlap(32, 39, 39, 42)
    assert overlap == (True, 39, 39)
    no_overlap = _overlap(10, 20, 30, 40)
    assert no_overlap == (False, "", "")
