from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Normalized TexasET observations JSON")
    parser.add_argument("--json-output", default="data/nrhis/texaset/latest_texaset_regions.json")
    parser.add_argument("--markdown-output", default="data/nrhis/texaset/latest_texaset_regions.md")
    parser.add_argument("--repository-root", default=".")
    args = parser.parse_args()
    root = Path(args.repository_root).resolve()
    sys.path.insert(0, str(root / "src"))
    from nrhis_harvest.texaset_et_harvest import TexasETObservation, build_regional_summary, render_markdown

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    observations = [TexasETObservation.from_mapping(row) for row in payload.get("observations", [])]
    summary = build_regional_summary(observations, generated_at=datetime.now(timezone.utc))
    json_path = root / args.json_output
    md_path = root / args.markdown_output
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(summary), encoding="utf-8")
    print(json_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
