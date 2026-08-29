from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from nrhis_analysis.usgs_history_query import (
    DEFAULT_STRIDE_ROWS,
    QueryError,
    build_sparse_index,
    load_sparse_index,
    write_query_bundle,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query the finalized NRHIS historical USGS archive with zero network requests."
    )
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--site", action="append", default=[])
    parser.add_argument("--parameter", action="append", default=[])
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--stride-rows", type=int, default=DEFAULT_STRIDE_ROWS)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--rebuild-index", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.csv = args.csv.resolve()
    args.index = args.index.resolve()
    args.output_root = args.output_root.resolve()

    if args.rebuild_index or not args.index.exists():
        index = build_sparse_index(args.csv, args.index, stride_rows=args.stride_rows)
        print(
            f"Historical query index ready: {index['total_rows']} rows, "
            f"{len(index['entries'])} sparse offsets"
        )
    else:
        try:
            load_sparse_index(args.index, args.csv)
        except QueryError:
            index = build_sparse_index(args.csv, args.index, stride_rows=args.stride_rows)
            print(
                f"Historical query index rebuilt: {index['total_rows']} rows, "
                f"{len(index['entries'])} sparse offsets"
            )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_root / f"query-{stamp}"
    receipt = write_query_bundle(
        args.csv,
        args.index,
        output_dir,
        start=args.start,
        end=args.end,
        site_nos=args.site,
        parameter_codes=args.parameter,
        limit=args.limit,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except QueryError as exc:
        raise SystemExit(f"NRHIS historical query failed: {exc}") from exc
