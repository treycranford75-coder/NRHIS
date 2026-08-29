from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_python_query_cli_bootstraps_src_import_path() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/query_usgs_history.py", "--help"],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Query the finalized NRHIS historical USGS archive" in result.stdout
    script = Path("scripts/query_usgs_history.py").read_text(encoding="utf-8")
    assert 'Path(__file__).resolve().parents[1] / "src"' in script
    assert "sys.path.insert(0, str(_src))" in script


def test_powershell_wrapper_normalizes_cross_process_array_values() -> None:
    script = Path("scripts/Query-USGS-History.ps1").read_text(encoding="utf-8")
    assert "$NormalizedSiteNos = @(" in script
    assert "$NormalizedParameterCodes = @(" in script
    assert "([string]$raw -split ',')" in script
    assert "foreach ($site in $NormalizedSiteNos)" in script
    assert "foreach ($parameter in $NormalizedParameterCodes)" in script
    assert 'Write-Host "Params: $($NormalizedParameterCodes -join \', \')"' in script
    assert "foreach ($site in $SiteNo)" not in script
    assert "foreach ($parameter in $ParameterCode)" not in script
