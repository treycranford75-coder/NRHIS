from __future__ import annotations
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from nrhis_harvest.basin_operational_snapshot import build_snapshot

FIX=Path(__file__).parent/'fixtures'/'build054'

def _setup(tmp_path: Path) -> tuple[Path,Path]:
    data=tmp_path/'data'
    (data/'current').mkdir(parents=True)
    (data/'nwps').mkdir(parents=True)
    (data/'quality').mkdir(parents=True)
    shutil.copy(FIX/'usgs_current_conditions.json',data/'current'/'usgs_current_conditions.json')
    shutil.copy(FIX/'nwps_readiness.json',data/'nwps'/'nwps_readiness.json')
    shutil.copy(FIX/'usgs_data_quality_summary.json',data/'quality'/'usgs_data_quality_summary.json')
    cfg=tmp_path/'config.json'
    cfg.write_text(json.dumps({'stations':[{'site_no':'08210000','name':'Three Rivers','display_order':1,'required_parameters':['00060','00065']},{'site_no':'08211200','name':'Bluntzer','display_order':2,'required_parameters':['00060','00065','00095']}]}),encoding='utf-8')
    return cfg,data

def test_integrates_observations_forecasts_and_tds(tmp_path: Path) -> None:
    cfg,data=_setup(tmp_path)
    receipt=build_snapshot(cfg,data,generated_at=datetime(2026,7,19,21,tzinfo=timezone.utc))
    snap=json.loads((data/'operational'/'basin_operational_snapshot.json').read_text())
    assert snap['station_count']==2
    assert snap['highest_forecast_category']=='minor'
    bluntzer=next(r for r in snap['stations'] if r['site_no']=='08211200')
    assert bluntzer['observed_discharge_cfs']==64.0
    assert bluntzer['estimated_tds_mg_l']==1170.0
    assert Path(receipt['receipt_path']).exists()

def test_missing_required_parameter_blocks_reporting(tmp_path: Path) -> None:
    cfg,data=_setup(tmp_path)
    rows=json.loads((data/'current'/'usgs_current_conditions.json').read_text())
    rows=[r for r in rows if not (r['site_no']=='08211200' and r['parameter_code']=='00095')]
    (data/'current'/'usgs_current_conditions.json').write_text(json.dumps(rows),encoding='utf-8')
    build_snapshot(cfg,data)
    snap=json.loads((data/'operational'/'basin_operational_snapshot.json').read_text())
    assert snap['ready_for_reporting'] is False
    assert snap['blocking_station_count']==1
