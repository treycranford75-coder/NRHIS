from __future__ import annotations
import argparse
import json
from pathlib import Path
from nrhis_harvest.reservoir_response import run

p = argparse.ArgumentParser()
p.add_argument("--config", default="config/nrhis/reservoir_response.json")
p.add_argument("--data-root", default="data/nrhis")
a = p.parse_args()
print(json.dumps(run(Path(a.config), Path(a.data_root)), indent=2))
