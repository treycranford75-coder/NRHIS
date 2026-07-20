from __future__ import annotations
from nrhis_harvest.reservoir_response import cfs_hours_to_acft, estimate_responses

def config():
    return {
        'routing_capture_factors': {'ChokeCanyon': {'low': .5, 'central': .6, 'high': .7}},
        'routing_windows_hours': {'ChokeCanyon': 24},
        'reservoirs': {'ChokeCanyon': {'display_name': 'Choke Canyon Reservoir'}},
    }

def test_conversion():
    assert cfs_hours_to_acft(1000, 24) == 1983.47

def test_estimate_response():
    reservoirs=[{'reservoir_id':'ChokeCanyon','reservoir_name':'Choke Canyon Reservoir','conservation_storage_acft':200000,'conservation_capacity_acft':700000,'percent_full':28.6}]
    forecasts=[{'station_id':'08200000','forecast_peak_flow_cfs':1000}]
    row=estimate_responses(reservoirs, forecasts, config())[0]
    assert row.estimated_event_gain_central_acft == 1190.08
    assert row.projected_storage_central_acft == 201190.08
    assert row.confidence == 'moderate'
    assert 'latest available hydrographs' in row.caveat

def test_low_confidence_without_forecast():
    row=estimate_responses([{'reservoir_id':'ChokeCanyon','conservation_storage_acft':200000,'conservation_capacity_acft':700000}], [], config())[0]
    assert row.confidence == 'low'
    assert row.estimated_event_gain_low_acft is None
