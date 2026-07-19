"""Command-line entry point for the NRHIS USGS harvest engine."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

from .registry import RegistryError
from .service import harvest_usgs
from .usgs import UsgsError


def _date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Harvest USGS NWIS observations for NRHIS")
    parser.add_argument("--registry", type=Path, required=True, help="YAML station registry")
    parser.add_argument("--output-root", type=Path, default=Path("data"))
    parser.add_argument("--start", type=_date)
    parser.add_argument("--end", type=_date)
    parser.add_argument("--days", type=int, default=2, help="Lookback when --start is omitted")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--log-file", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.days < 1:
        parser.error("--days must be at least 1")
    end = args.end or date.today()
    start = args.start or (end - timedelta(days=args.days - 1))
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if args.log_file:
        args.log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(args.log_file, encoding="utf-8"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)sZ %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        handlers=handlers,
        force=True,
    )
    try:
        result = harvest_usgs(
            args.registry,
            args.output_root,
            start,
            end,
            timeout_seconds=args.timeout,
        )
    except (RegistryError, UsgsError, OSError, ValueError) as exc:
        logging.getLogger(__name__).error("Harvest failed: %s", exc)
        return 1
    print(f"Run ID: {result.run_id}")
    print(f"Stations: {result.station_count}")
    print(f"Observations: {result.observation_count}")
    print(f"Raw: {result.raw_path}")
    print(f"Normalized: {result.normalized_path}")
    print(f"Metadata: {result.metadata_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
