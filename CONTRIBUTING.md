# Contributing

1. Do not overwrite raw source data.
2. Put experimental work on a feature branch.
3. Add or update tests when changing calculations.
4. Record material engineering decisions in `docs/Standards/` or the applicable event notebook.
5. Do not commit credentials, API keys, virtual environments, caches, or large raw datasets.
---

## Local development quick start

NRHIS requires Python 3.11 or later.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
.\scripts\Verify-Environment.ps1
```

Before opening a pull request:

```powershell
python -m pytest -q
python -m ruff check .
git diff --check
```

See `docs/Development/DEV_SETUP.md` for the full setup and troubleshooting guide.
