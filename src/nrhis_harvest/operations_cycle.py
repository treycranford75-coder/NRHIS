"""Build063 resilient twice-daily NRHIS operations-cycle orchestration."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence


@dataclass(frozen=True)
class CycleStep:
    name: str
    script: str
    arguments: tuple[str, ...] = ()
    required: bool = True


@dataclass(frozen=True)
class StepResult:
    name: str
    command: list[str]
    status: str
    exit_code: int
    started_at: str
    completed_at: str
    log_path: str
    required: bool


DEFAULT_STEPS: tuple[CycleStep, ...] = (
    CycleStep("usgs_current", "Harvest-USGS-Production.ps1"),
    CycleStep("usgs_incremental", "Update-USGS-Incremental.ps1"),
    CycleStep("nwps_forecasts", "Harvest-NWPS-Forecasts.ps1"),
    CycleStep("twdb_reservoirs", "Harvest-TWDB-Reservoirs.ps1"),
    CycleStep("reservoir_water_budget", "Build-Reservoir-Water-Budget.ps1"),
    CycleStep("reservoir_response", "Estimate-Reservoir-Response.ps1"),
    CycleStep("reservoir_operations", "Build-Reservoir-Operations-Summary.ps1"),
    CycleStep("salt03_coastal", "Harvest-SALT03-Coastal.ps1"),
    CycleStep("integrated_snapshot", "Build-Integrated-Operations-Snapshot.ps1"),
    CycleStep("publication_bundle", "Build-Publication-Bundle.ps1"),
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _stamp(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8", newline="")
    temp.replace(path)


def build_steps(config: dict, *, qa_passes_completed: int) -> list[CycleStep]:
    disabled = set(config.get("disabled_steps", []))
    required_overrides = config.get("required_steps", {})
    steps: list[CycleStep] = []
    for step in DEFAULT_STEPS:
        if step.name in disabled:
            continue
        arguments = step.arguments
        if step.name == "publication_bundle":
            arguments = ("-QaPassesCompleted", str(qa_passes_completed))
        steps.append(
            CycleStep(
                name=step.name,
                script=step.script,
                arguments=arguments,
                required=bool(required_overrides.get(step.name, step.required)),
            )
        )
    return steps


def _default_runner(
    command: Sequence[str],
    cwd: Path,
    timeout_seconds: int = 300,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            list(command),
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        return subprocess.CompletedProcess(
            args=list(command),
            returncode=124,
            stdout=stdout,
            stderr=stderr + f"\nNRHIS step timed out after {timeout_seconds} seconds.\n",
        )


def run_cycle(
    config_path: Path,
    repository_root: Path,
    *,
    qa_passes_completed: int = 0,
    cycle_name: str | None = None,
    runner: Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]] | None = None,
    now: Callable[[], datetime] = utc_now,
) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    repository_root = repository_root.resolve()
    if not (repository_root / ".git").exists():
        raise RuntimeError(f"NRHIS repository root not found: {repository_root}")

    started = now()
    cycle_id = cycle_name or started.strftime("%Y%m%dT%H%M%SZ")
    evidence_root = repository_root / config.get(
        "evidence_directory", "data/nrhis/operations_cycles"
    )
    cycle_root = evidence_root / cycle_id
    logs_root = cycle_root / "logs"
    scripts_root = repository_root / config.get("scripts_directory", "scripts")
    shell = str(config.get("powershell_executable", "powershell.exe"))
    stop_on_required_failure = bool(config.get("stop_on_required_failure", True))
    timeout_seconds = int(config.get("step_timeout_seconds", 300))
    invoke = runner or (lambda command, cwd: _default_runner(command, cwd, timeout_seconds))

    results: list[StepResult] = []
    blocked = False
    for step in build_steps(config, qa_passes_completed=qa_passes_completed):
        script_path = scripts_root / step.script
        if not script_path.exists():
            started_step = now()
            completed_step = now()
            log_path = logs_root / f"{step.name}.log"
            message = f"Missing operational script: {script_path}\n"
            _atomic_write(log_path, message)
            result = StepResult(
                name=step.name,
                command=[],
                status="failed" if step.required else "skipped",
                exit_code=127,
                started_at=_stamp(started_step),
                completed_at=_stamp(completed_step),
                log_path=str(log_path),
                required=step.required,
            )
        else:
            command = [
                shell,
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
                *step.arguments,
            ]
            started_step = now()
            completed = invoke(command, repository_root)
            completed_step = now()
            log_path = logs_root / f"{step.name}.log"
            output = (completed.stdout or "") + (completed.stderr or "")
            _atomic_write(log_path, output)
            result = StepResult(
                name=step.name,
                command=command,
                status="passed" if completed.returncode == 0 else "failed",
                exit_code=int(completed.returncode),
                started_at=_stamp(started_step),
                completed_at=_stamp(completed_step),
                log_path=str(log_path),
                required=step.required,
            )
        results.append(result)
        if result.status == "failed" and result.required and stop_on_required_failure:
            blocked = True
            break

    completed_at = now()
    required_failures = [r.name for r in results if r.required and r.status != "passed"]
    status = "failed" if required_failures else "completed"
    publication_authorized = status == "completed" and qa_passes_completed >= 2
    receipt = {
        "schema_version": 1,
        "build": "063",
        "cycle_id": cycle_id,
        "started_at": _stamp(started),
        "completed_at": _stamp(completed_at),
        "status": status,
        "blocked": blocked,
        "qa_passes_completed": qa_passes_completed,
        "publication_authorized": publication_authorized,
        "step_timeout_seconds": timeout_seconds,
        "required_failures": required_failures,
        "steps": [asdict(item) for item in results],
    }
    receipt_path = cycle_root / "operations_cycle_receipt.json"
    latest_path = evidence_root / "latest_operations_cycle.json"
    _atomic_write(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    _atomic_write(latest_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    receipt["receipt_path"] = str(receipt_path)
    receipt["latest_path"] = str(latest_path)
    return receipt
