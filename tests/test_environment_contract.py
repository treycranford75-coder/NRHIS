"""Tests for the documented NRHIS development-environment contract."""

from __future__ import annotations

import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = REPOSITORY_ROOT / "pyproject.toml"
VERIFY_SCRIPT = REPOSITORY_ROOT / "scripts" / "Verify-Environment.ps1"
DEV_SETUP = REPOSITORY_ROOT / "docs" / "Development" / "DEV_SETUP.md"

REQUIRED_RUNTIME_DEPENDENCIES = {"pandas", "pyyaml", "requests"}
REQUIRED_DEV_DEPENDENCIES = {"pytest", "ruff"}


def _normalized_dependency_name(specification: str) -> str:
    name = specification.split(";", maxsplit=1)[0]
    for separator in ("[", "<", ">", "=", "!", "~"):
        name = name.split(separator, maxsplit=1)[0]
    return name.strip().lower()


def test_pyproject_declares_supported_python_and_dependencies() -> None:
    project = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))["project"]
    assert project["requires-python"] == ">=3.11"

    runtime_dependencies = {
        _normalized_dependency_name(item) for item in project.get("dependencies", [])
    }
    assert REQUIRED_RUNTIME_DEPENDENCIES <= runtime_dependencies

    optional_dependencies = project.get("optional-dependencies", {})
    dev_dependencies = {
        _normalized_dependency_name(item) for item in optional_dependencies.get("dev", [])
    }
    assert REQUIRED_DEV_DEPENDENCIES <= dev_dependencies


def test_environment_verification_script_exists_and_checks_core_tools() -> None:
    text = VERIFY_SCRIPT.read_text(encoding="utf-8-sig")
    assert 'Assert-Command -Name "git"' in text
    assert 'Assert-Command -Name "python"' in text
    assert "python -m pytest -q" in text
    assert "python -m ruff check ." in text


def test_developer_setup_documents_reproducible_commands() -> None:
    text = DEV_SETUP.read_text(encoding="utf-8-sig")
    required_commands = (
        "python -m venv .venv",
        'python -m pip install -e ".[dev]"',
        r".\scripts\Verify-Environment.ps1",
        "python -m pytest -q",
        "python -m ruff check .",
        r".\scripts\Harvest-USGS.ps1",
    )
    for command in required_commands:
        assert command in text
