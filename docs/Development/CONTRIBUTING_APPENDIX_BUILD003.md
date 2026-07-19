# CONTRIBUTING.md Build003 Appendix

Append the following section to the existing root-level `CONTRIBUTING.md`.

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
