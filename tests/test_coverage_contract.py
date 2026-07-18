"""Tests for the Build004 coverage and CI quality contract."""

from __future__ import annotations

import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = REPOSITORY_ROOT / "pyproject.toml"
CI_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml"


def _dependency_names(specifications: list[str]) -> set[str]:
    names: set[str] = set()
    for specification in specifications:
        name = specification
        for separator in ("[", "<", ">", "=", "!", "~"):
            name = name.split(separator, maxsplit=1)[0]
        names.add(name.strip().lower())
    return names


def test_dev_dependencies_include_coverage_tools() -> None:
    document = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    dev_dependencies = document["project"]["optional-dependencies"]["dev"]
    names = _dependency_names(dev_dependencies)

    assert {"coverage", "pytest-cov"} <= names


def test_coverage_configuration_enforces_branch_floor() -> None:
    document = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))

    run_config = document["tool"]["coverage"]["run"]
    report_config = document["tool"]["coverage"]["report"]
    xml_config = document["tool"]["coverage"]["xml"]

    assert run_config["branch"] is True
    assert run_config["source"] == ["src"]
    assert "src/nrhis_calibration/legacy/*" in run_config["omit"]
    assert report_config["fail_under"] == 80
    assert report_config["show_missing"] is True
    assert xml_config["output"] == "coverage.xml"


def test_ci_enforces_coverage_and_uploads_xml() -> None:
    workflow = CI_PATH.read_text(encoding="utf-8")

    required_fragments = (
        "--cov=src",
        "--cov-branch",
        "--cov-report=term-missing",
        "--cov-report=xml",
        "--cov-fail-under=80",
        "actions/upload-artifact@v4",
        "path: coverage.xml",
    )

    for fragment in required_fragments:
        assert fragment in workflow
