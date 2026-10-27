from pathlib import Path
import json

import numpy as np
import pandas as pd

from genco_ops.results import regenerate


ROOT=Path(__file__).resolve().parents[1]


def test_texas_search_accounting_and_reference_identity(tmp_path):
    tables=ROOT/'experiments/texas2k/results/stage_m/tables'
    candidates=pd.read_parquet(tables/'candidate_results.parquet')
    calls=pd.read_parquet(tables/'continuous_evaluations.parquet')
    release=json.loads((ROOT/'artifacts/release_coverage.json').read_text())
    coverage=release['completed']
    searches=coverage['GENCO_full_searches']+coverage.get('OpenGridSFM_full_searches',0)
    assert 3<=searches<=6
    assert len(candidates)==301*searches and len(calls)==6020*searches
    assert candidates.k.le(2).all()
    assert candidates.groupby('model').size().eq(301).all()
    assert calls.groupby(['model','topology_key']).size().eq(20).all()
    exact=pd.read_csv(tables/'finalist_native_and_exact.csv')
    np.testing.assert_allclose(exact.a_j,.8*exact.a_r+.2*exact.shed,rtol=1e-12,atol=1e-12)
    result=regenerate(ROOT,'texas2k',tmp_path)
    assert result['completed_searches']==searches
    assert result['phase_i_complete'] is release['phase_i_complete']
    assert release['phase_ii']=='HELD_BY_USER'
    if release['phase_i_complete']:
        gate=json.loads((ROOT/'experiments/texas2k/results/stage_m/provenance/completion_v159/phase_gate.json').read_text())
        assert gate['gate']=='PHASE_I_RESULTS_COMPLETE' and gate['status']=='PASS'
        assert gate['required_cases']==1600 and len(gate['completed_fits'])==8
        assert len(gate['results'])==searches
        assert all(row['evaluated_states']==301 for row in gate['results'])
    regenerated=pd.read_csv(tmp_path/'regenerated_reference_summary.csv')
    pd.testing.assert_frame_equal(regenerated,exact)


def test_goc_population_is_not_texas_or_demo_population(tmp_path):
    result=regenerate(ROOT,'goc_500',tmp_path)
    assert result['evaluation_only'] is True
    original=pd.read_csv(ROOT/'experiments/goc_500/results/ft6_test_metrics.csv')
    regenerated=pd.read_csv(tmp_path/'regenerated_test_metrics.csv')
    pd.testing.assert_frame_equal(original,regenerated)
