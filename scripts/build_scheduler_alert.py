from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _severity(problems: list[str]) -> str:
    if not problems:
        return "info"
    critical_prefixes = (
        "missing_",
        "invalid_",
        "scheduler_exit_code:",
        "scheduler_status:",
        "latest_cycle_status:",
        "missed_schedule_slot:",
    )
    if any(problem.startswith(critical_prefixes) for problem in problems):
        return "critical"
    return "warning"


def build_alert(health: dict[str, Any]) -> dict[str, Any]:
    problems = [str(item) for item in health.get("problems", [])]
    severity = _severity(problems)
    healthy = bool(health.get("healthy", False)) and not problems
    status = "clear" if healthy else "active"
    summary = (
        "NRHIS scheduler health is clear."
        if healthy
        else f"NRHIS scheduler health has {len(problems)} active problem(s)."
    )
    return {
        "schema_version": 1,
        "build": "069",
        "source_build": str(health.get("build", "unknown")),
        "checked_at": health.get("checked_at"),
        "status": status,
        "severity": severity,
        "healthy": healthy,
        "summary": summary,
        "problems": problems,
        "tasks": health.get("tasks", []),
        "source_files": health.get("files", {}),
    }


def _markdown(alert: dict[str, Any]) -> str:
    lines = [
        "# NRHIS Scheduler Alert",
        "",
        f"- Status: **{alert['status']}**",
        f"- Severity: **{alert['severity']}**",
        f"- Checked at: `{alert.get('checked_at') or 'unknown'}`",
        f"- Summary: {alert['summary']}",
        "",
        "## Problems",
        "",
    ]
    problems = alert["problems"]
    if problems:
        lines.extend(f"- `{problem}`" for problem in problems)
    else:
        lines.append("- None")
    lines.extend(["", "## Scheduled Tasks", ""])
    tasks = alert.get("tasks", [])
    if tasks:
        for task in tasks:
            lines.append(
                f"- {task.get('task_name', 'unknown')}: "
                f"state={task.get('state', 'unknown')}, "
                f"healthy={task.get('healthy', False)}"
            )
    else:
        lines.append("- No task records")
    return "\n".join(lines) + "\n"


def _append_history(path: Path, alert: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fingerprint = (alert.get("checked_at"), alert.get("status"), tuple(alert.get("problems", [])))
    if path.exists():
        last_line = ""
        with path.open("r", encoding="utf-8-sig") as handle:
            for line in handle:
                if line.strip():
                    last_line = line
        if last_line:
            try:
                previous = json.loads(last_line)
                previous_fingerprint = (
                    previous.get("checked_at"),
                    previous.get("status"),
                    tuple(previous.get("problems", [])),
                )
                if previous_fingerprint == fingerprint:
                    return
            except json.JSONDecodeError:
                pass
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(alert, sort_keys=True) + "\n")


def run(repository_root: Path, config_path: Path) -> dict[str, Any]:
    config = _load_json(config_path)
    health_path = repository_root / str(config["scheduler_health_json"])
    alert_json_path = repository_root / str(config["output_json"])
    alert_markdown_path = repository_root / str(config["output_markdown"])
    history_path = repository_root / str(config["history_jsonl"])
    receipt_path = repository_root / str(config["output_receipt"])

    health = _load_json(health_path)
    alert = build_alert(health)

    alert_json_path.parent.mkdir(parents=True, exist_ok=True)
    alert_json_path.write_text(
        json.dumps(alert, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    alert_markdown_path.parent.mkdir(parents=True, exist_ok=True)
    alert_markdown_path.write_text(_markdown(alert), encoding="utf-8")
    _append_history(history_path, alert)

    receipt = {
        "schema_version": 1,
        "build": "069",
        "completed_at": alert.get("checked_at"),
        "status": "completed",
        "alert_status": alert["status"],
        "severity": alert["severity"],
        "problem_count": len(alert["problems"]),
        "files": {
            "json": str(alert_json_path),
            "markdown": str(alert_markdown_path),
            "history": str(history_path),
        },
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    alert["receipt_path"] = str(receipt_path)
    return alert


def main() -> int:
    parser = argparse.ArgumentParser(description="Build NRHIS scheduler alert artifacts")
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--config", default="config/nrhis/scheduler_alert.json")
    parser.add_argument("--fail-on-alert", action="store_true")
    args = parser.parse_args()
    result = run(Path(args.repository_root).resolve(), Path(args.config).resolve())
    print(json.dumps(result, indent=2))
    return 1 if args.fail_on_alert and result["status"] == "active" else 0


if __name__ == "__main__":
    raise SystemExit(main())
