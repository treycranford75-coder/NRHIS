#!/usr/bin/env python3
"""Pass 1 Upper Nueces travel-time calibration, optimized edition."""
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import requests

BASE = "https://waterservices.usgs.gov/nwis/iv/"
SITES = {"laguna": "08190000", "uvalde": "08192000"}
PARAM = "00060"


def log(msg: str) -> None:
    print(msg, flush=True)


def fetch_block(site: str, start: str, end: str, out: Path, retries: int = 5) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and out.stat().st_size > 100:
        log(f"  Using cached {out.name}")
        return out
    params = {
        "format": "json", "sites": site, "parameterCd": PARAM,
        "startDT": start, "endDT": end, "siteStatus": "all"
    }
    last = None
    for attempt in range(1, retries + 1):
        try:
            log(f"  Download {site} {start} to {end} (attempt {attempt})")
            response = requests.get(BASE, params=params, timeout=180)
            response.raise_for_status()
            out.write_bytes(response.content)
            return out
        except Exception as exc:
            last = exc
            if attempt < retries:
                time.sleep(min(30, 2 ** attempt))
    raise RuntimeError(f"Failed {site} {start} {end}: {last}")


def parse_json(path: Path) -> pd.DataFrame:
    """Parse one USGS JSON block using vectorized datetime conversion."""
    obj = json.loads(path.read_text(encoding="utf-8"))
    sites: list[str] = []
    timestamps: list[str] = []
    values: list[float] = []
    qualifiers: list[str] = []

    for ts in obj.get("value", {}).get("timeSeries", []):
        variable = ts.get("variable", {}).get("variableCode", [{}])[0].get("value")
        if variable != PARAM:
            continue
        site = ts.get("sourceInfo", {}).get("siteCode", [{}])[0].get("value")
        for block in ts.get("values", []):
            for item in block.get("value", []):
                sites.append(site)
                timestamps.append(item.get("dateTime", ""))
                try:
                    values.append(float(item.get("value")))
                except (TypeError, ValueError):
                    values.append(np.nan)
                qualifiers.append(";".join(item.get("qualifiers", [])))

    if not timestamps:
        return pd.DataFrame(columns=["site_no", "datetime_utc", "discharge_cfs", "qualifier"])

    # ISO8601 avoids pandas' expensive per-element format inference.
    dt = pd.to_datetime(pd.Series(timestamps), format="ISO8601", utc=True, errors="coerce")
    df = pd.DataFrame({
        "site_no": sites,
        "datetime_utc": dt,
        "discharge_cfs": values,
        "qualifier": qualifiers,
    })
    df = df.dropna(subset=["datetime_utc"])
    return df.drop_duplicates(["site_no", "datetime_utc"]).sort_values("datetime_utc")


def water_year_blocks(start_wy: int, end_wy: int):
    for wy in range(start_wy, end_wy + 1):
        yield wy, f"{wy - 1}-10-01", f"{wy}-09-30"


def hourly_series(df: pd.DataFrame) -> pd.Series:
    s = df.set_index("datetime_utc")["discharge_cfs"].sort_index()
    s = s[~s.index.duplicated(keep="last")]
    return s.resample("1h").median()


def audit(s: pd.Series, site: str) -> dict:
    expected = len(pd.date_range(s.index.min(), s.index.max(), freq="1h", tz="UTC")) if len(s) else 0
    valid = int(s.notna().sum())
    return {
        "site_no": site,
        "start_utc": str(s.index.min()) if len(s) else None,
        "end_utc": str(s.index.max()) if len(s) else None,
        "expected_hourly": expected,
        "valid_hourly": valid,
        "completeness_pct": round(100 * valid / expected, 2) if expected else 0,
    }


def detect_events(s: pd.Series, min_peak: float = 100.0, separation_h: int = 120) -> pd.DataFrame:
    x = s.interpolate(limit=3).rolling(3, center=True, min_periods=1).median()
    vals = x.to_numpy()
    cand = []
    for i in range(1, len(vals) - 1):
        if np.isfinite(vals[i]) and vals[i] >= min_peak and vals[i] >= vals[i - 1] and vals[i] > vals[i + 1]:
            cand.append((i, vals[i]))
    chosen = []
    for i, value in sorted(cand, key=lambda item: item[1], reverse=True):
        if all(abs(i - j) >= separation_h for j, _ in chosen):
            chosen.append((i, value))
    chosen.sort()
    return pd.DataFrame({
        "peak_time_utc": [x.index[i] for i, _ in chosen],
        "peak_cfs": [value for _, value in chosen],
    })


def event_features(s: pd.Series, peak_time: pd.Timestamp, pre_h: int = 120, post_h: int = 240):
    w = s.loc[peak_time - pd.Timedelta(hours=pre_h): peak_time + pd.Timedelta(hours=post_h)].copy()
    if w.notna().sum() < 48:
        return None
    baseline = float(w.iloc[: min(48, len(w))].median())
    peak = float(w.max())
    peak_at = w.idxmax()
    amplitude = peak - baseline
    if not np.isfinite(amplitude) or amplitude <= 0:
        return None
    out = {"baseline": baseline, "peak": peak, "peak_time": peak_at}
    for fraction in (0.10, 0.25, 0.50, 0.75):
        target = baseline + fraction * amplitude
        hit = w.loc[:peak_at]
        hit = hit[hit >= target]
        out[f"t{int(fraction * 100)}"] = hit.index[0] if len(hit) else pd.NaT
    return out


def best_corr_lag(up: pd.Series, dn: pd.Series, start, end, min_lag: int = 1, max_lag: int = 240):
    u = up.loc[start:end]
    d = dn.loc[start:end]
    idx = u.index.union(d.index)
    u = np.log1p(u.reindex(idx).clip(lower=0))
    d = np.log1p(d.reindex(idx).clip(lower=0))
    best_lag, best_r = np.nan, np.nan
    for lag in range(min_lag, max_lag + 1):
        z = pd.concat([u, d.shift(-lag)], axis=1).dropna()
        if len(z) < 36:
            continue
        corr = z.iloc[:, 0].corr(z.iloc[:, 1])
        if np.isfinite(corr) and (not np.isfinite(best_r) or corr > best_r):
            best_lag, best_r = lag, corr
    return best_lag, best_r


def match_events(up: pd.Series, dn: pd.Series, peaks: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total = len(peaks)
    for number, (_, record) in enumerate(peaks.iterrows(), start=1):
        if number == 1 or number % 10 == 0 or number == total:
            log(f"  Matching event {number}/{total}")
        t = record.peak_time_utc
        fu = event_features(up, t)
        if not fu:
            continue
        downstream_window = dn.loc[t + pd.Timedelta(hours=1): t + pd.Timedelta(hours=240)]
        if downstream_window.notna().sum() < 24:
            continue
        downstream_peak_at = downstream_window.idxmax()
        fd = event_features(dn, downstream_peak_at)
        if not fd:
            continue
        row = {
            "up_peak_time_utc": fu["peak_time"],
            "up_peak_cfs": fu["peak"],
            "dn_peak_time_utc": fd["peak_time"],
            "dn_peak_cfs": fd["peak"],
            "peak_lag_h": (fd["peak_time"] - fu["peak_time"]).total_seconds() / 3600,
        }
        for p in (10, 25, 50, 75):
            a, b = fu[f"t{p}"], fd[f"t{p}"]
            row[f"rise{p}_lag_h"] = (b - a).total_seconds() / 3600 if pd.notna(a) and pd.notna(b) else np.nan
        lag, corr = best_corr_lag(up, dn, t - pd.Timedelta(hours=120), t + pd.Timedelta(hours=360))
        row["xcorr_lag_h"] = lag
        row["xcorr_r"] = corr
        lag_values = [row["peak_lag_h"], row["rise25_lag_h"], row["rise50_lag_h"], row["xcorr_lag_h"]]
        good = [v for v in lag_values if np.isfinite(v) and 0 < v <= 240]
        row["class"] = "A" if len(good) >= 3 and corr >= 0.75 else ("B" if len(good) >= 2 and corr >= 0.55 else "C")
        rows.append(row)
    return pd.DataFrame(rows)


def flow_class(q):
    return pd.cut(
        pd.Series(q),
        [-np.inf, 100, 500, 2000, 10000, 30000, np.inf],
        labels=["<100", "100-500", "500-2,000", "2,000-10,000", "10,000-30,000", ">30,000"],
    ).iloc[0]


def summarize(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return events
    accepted = events[events["class"].isin(["A", "B"])].copy()
    accepted["flow_class_cfs"] = accepted["up_peak_cfs"].apply(flow_class)
    rows = []
    for flow_group, group in accepted.groupby("flow_class_cfs", observed=True):
        for metric in ["rise25_lag_h", "rise50_lag_h", "peak_lag_h", "xcorr_lag_h"]:
            z = group[metric].dropna()
            if len(z):
                rows.append({
                    "flow_class_cfs": str(flow_group), "metric": metric, "events": len(z),
                    "median_h": round(z.median(), 1), "p10_h": round(z.quantile(0.1), 1),
                    "p90_h": round(z.quantile(0.9), 1),
                })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-wy", type=int, default=2008)
    parser.add_argument("--end-wy", type=int, default=2026)
    parser.add_argument("--out", default="pass1_output")
    args = parser.parse_args()

    root = Path(args.out)
    raw = root / "raw"
    tables = root / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    frames = {name: [] for name in SITES}

    for name, site in SITES.items():
        log(f"\n{name.upper()} ({site})")
        for wy, start, end in water_year_blocks(args.start_wy, args.end_wy):
            path = fetch_block(site, start, end, raw / name / f"{site}_WY{wy}.json")
            log(f"  Parse WY{wy}")
            frame = parse_json(path)
            log(f"    {len(frame):,} observations")
            frames[name].append(frame)

    series = {}
    audits = []
    for name, site in SITES.items():
        log(f"\nConsolidating {name} ({site})")
        df = pd.concat(frames[name], ignore_index=True).drop_duplicates(["site_no", "datetime_utc"])
        df = df.sort_values("datetime_utc")
        df.to_csv(tables / f"{site}_instantaneous.csv", index=False)
        series[name] = hourly_series(df)
        series[name].to_csv(tables / f"{site}_hourly.csv", header=["discharge_cfs"])
        audits.append(audit(series[name], site))

    pd.DataFrame(audits).to_csv(tables / "completeness_audit.csv", index=False)
    log("\nDetecting Laguna events")
    peaks = detect_events(series["laguna"], min_peak=100)
    log(f"  {len(peaks)} candidate events")
    peaks.to_csv(tables / "laguna_candidate_events.csv", index=False)

    log("\nMatching events to Uvalde")
    events = match_events(series["laguna"], series["uvalde"], peaks)
    events.to_csv(tables / "matched_event_lags.csv", index=False)
    summary = summarize(events)
    summary.to_csv(tables / "calibration_lookup.csv", index=False)

    log(f"\nCOMPLETE: {root.resolve()}")
    log(pd.DataFrame(audits).to_string(index=False))
    log(summary.to_string(index=False) if not summary.empty else "No accepted events")


if __name__ == "__main__":
    main()
