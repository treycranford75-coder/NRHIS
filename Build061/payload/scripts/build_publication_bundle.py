from __future__ import annotations

import argparse
import json
from pathlib import Path

from nrhis_harvest.publication_bundle import run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/nrhis/publication_bundle.json")
    parser.add_argument("--data-root", default="data/nrhis")
    parser.add_argument("--qa-passes-completed", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(run(Path(args.config), Path(args.data_root), qa_passes_completed=args.qa_passes_completed), indent=2))


if __name__ == "__main__":
    main()
