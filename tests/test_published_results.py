from pathlib import Path

import numpy as np
import pandas as pd

from genco_ops.results import regenerate


ROOT=Path(__file__).resolve().parents[1]


def test_texas_search_accounting_and_reference_identity(tmp_path):
    tables=ROOT/'experiments/texas2k/results/stage_m/tables'
    candidates=pd.read_parquet(tables/'candidate_results.parquet')
    calls=pd.read_parquet(tables/'continuous_evaluations.parquet')
    assert len(candidates)==903 and len(calls)==18060
    assert candidates.k.le(2).all()
    assert candidates.groupby('model').size().eq(301).all()
    assert calls.groupby(['model','topology_key']).size().eq(20).all()
    exact=pd.read_csv(tables/'finalist_native_and_exact.csv')
    np.testing.assert_allclose(exact.a_j,.8*exact.a_r+.2*exact.shed,rtol=1e-12,atol=1e-12)
    result=regenerate(ROOT,'texas2k',tmp_path)
    assert result['completed_searches']==3
    regenerated=pd.read_csv(tmp_path/'regenerated_reference_summary.csv')
    pd.testing.assert_frame_equal(regenerated,exact)


def test_goc_population_is_not_texas_or_demo_population(tmp_path):
    result=regenerate(ROOT,'goc_500',tmp_path)
    assert result['evaluation_only'] is True
    original=pd.read_csv(ROOT/'experiments/goc_500/results/ft6_test_metrics.csv')
    regenerated=pd.read_csv(tmp_path/'regenerated_test_metrics.csv')
    pd.testing.assert_frame_equal(original,regenerated)
