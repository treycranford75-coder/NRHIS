from __future__ import annotations
import argparse
import json
from datetime import date
from pathlib import Path
from nrhis_harvest.reservoir_water_budget import run

p = argparse.ArgumentParser()
p.add_argument("--config", default="config/nrhis/reservoir_water_budget.json")
p.add_argument("--data-root", default="data/nrhis")
p.add_argument("--date")
a = p.parse_args()
print(
    json.dumps(
        run(
            Path(a.config),
            Path(a.data_root),
            report_date=date.fromisoformat(a.date) if a.date else None,
        ),
        indent=2,
    )
)
