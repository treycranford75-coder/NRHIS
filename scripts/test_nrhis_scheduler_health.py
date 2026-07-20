from __future__ import annotations

import argparse
import csv
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        temp = Path(handle.name)
    temp.replace(path)


def _load_optional(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _scheduled_tasks(prefix: str) -> dict[str, dict[str, Any]]:
    ps = (
        "Get-ScheduledTask | Where-Object {$_.TaskName -like '" + prefix.replace("'", "''") + "*'} | "
        "ForEach-Object { $i = Get-ScheduledTaskInfo -TaskName $_.TaskName; "
        "[pscustomobject]@{TaskName=$_.TaskName;State=[string]$_.State;LastRunTime=$i.LastRunTime;"
        "LastTaskResult=$i.LastTaskResult;NextRunTime=$i.NextRunTime} } | ConvertTo-Json -Depth 4"
    )
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", ps],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        return {}
    raw = completed.stdout.strip()
    if not raw:
        return {}
    parsed = json.loads(raw)
    rows = parsed if isinstance(parsed, list) else [parsed]
    return {str(row.get("TaskName")): row for row in rows}


def evaluate(repository_root: Path, config: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    now = now or _now()
    prefix = str(config.get("task_name_prefix", "NRHIS Operations - "))
    tasks = _scheduled_tasks(prefix)
    rows: list[dict[str, Any]] = []
    problems: list[str] = []
    for slot in config.get("expected_slots", []):
        label = str(slot["name"])
        task_name = prefix + label
        task = tasks.get(task_name)
        installed = task is not None
        state = str(task.get("State")) if task else "Missing"
        healthy = installed and state in {"Ready", "Running"}
        if not installed:
            problems.append(f"missing_task:{task_name}")
        elif not healthy:
            problems.append(f"task_state:{task_name}:{state}")
        rows.append({"task_name": task_name, "installed": installed, "state": state, "healthy": healthy})

    latest_cycle_path = repository_root / str(config["operations_cycle_latest"])
    latest_cycle = _load_optional(latest_cycle_path)
    if not latest_cycle:
        problems.append("missing_latest_operations_cycle")
    elif latest_cycle.get("status") != "completed":
        problems.append(f"latest_cycle_status:{latest_cycle.get('status')}")

    scheduler_receipt_path = repository_root / str(config["scheduler_receipt"])
    scheduler_receipt = _load_optional(scheduler_receipt_path)
    if not scheduler_receipt:
        problems.append("missing_scheduler_run_receipt")
    elif int(scheduler_receipt.get("exit_code", 1)) != 0:
        problems.append(f"scheduler_exit_code:{scheduler_receipt.get('exit_code')}")

    status = "healthy" if not problems else "unhealthy"
    return {
        "schema_version": 1,
        "build": "066",
        "checked_at": now.isoformat().replace("+00:00", "Z"),
        "status": status,
        "healthy": status == "healthy",
        "problems": problems,
        "tasks": rows,
        "files": {
            "latest_cycle": str(latest_cycle_path),
            "scheduler_receipt": str(scheduler_receipt_path),
        },
    }


def run(repository_root: Path, config_path: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    result = evaluate(repository_root, config)
    json_path = repository_root / str(config["output_json"])
    csv_path = repository_root / str(config["output_csv"])
    receipt_path = repository_root / str(config["output_receipt"])
    _atomic_write(json_path, json.dumps(result, indent=2, sort_keys=True) + "\n")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["task_name", "installed", "state", "healthy"])
        writer.writeheader()
        writer.writerows(result["tasks"])
    receipt = {
        "schema_version": 1,
        "build": "066",
        "completed_at": result["checked_at"],
        "status": result["status"],
        "problem_count": len(result["problems"]),
        "files": {"json": str(json_path), "csv": str(csv_path)},
    }
    _atomic_write(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    result["receipt_path"] = str(receipt_path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check NRHIS scheduled operations health")
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--config", default="config/nrhis/scheduler_health.json")
    parser.add_argument("--fail-on-unhealthy", action="store_true")
    args = parser.parse_args()
    result = run(Path(args.repository_root).resolve(), Path(args.config).resolve())
    print(json.dumps(result, indent=2))
    return 1 if args.fail_on_unhealthy and not result["healthy"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
