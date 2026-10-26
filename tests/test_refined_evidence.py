"""Guard the actual published study populations and their numerical identities."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from genco_ops.results import goc_comparison, study_coverage, texas_validation, texas_historical_comparison

ROOT = Path(__file__).resolve().parents[1]
GOC = ROOT / 'experiments/goc_500/results'


def test_added_retained_evidence_is_hash_bound_and_numeric_preservation_is_recorded():
    manifest = json.loads((ROOT / 'artifacts/results_provenance.json').read_text())
    assert len(manifest['files']) == 32
    for relative, item in manifest['files'].items():
        path = ROOT / relative
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item['published_sha256']
        assert item.get('numeric_columns_unchanged', item.get('numeric_values_unchanged')) is True
        if path.suffix == '.parquet':
            assert len(pd.read_parquet(path)) == item['rows']


def test_goc_refined_population_and_economic_a_tradeoff_identity():
    core = GOC / 'refined_study/core_results'
    candidates = pd.read_parquet(core / 'candidate_evaluations_all.parquet')
    assert candidates.groupby('method').size().tolist() == [30000] * 5
    refs = pd.read_parquet(core / 'reference_a_all.parquet')
    assert refs.groupby('method').size().tolist() == [15] * 5
    assert refs.reference_a_status.str.lower().eq('locally_solved').all()
    np.testing.assert_allclose(refs.reference_a_j_true,
        refs.lambda_r * refs.reference_a_r_norm_ac + (1 - refs.lambda_r) * refs.reference_a_l_shed_total,
        rtol=1e-10, atol=1e-10)
    comparison = goc_comparison(ROOT).set_index('model')
    assert comparison.loc['M0', 'finite_state_families'] == 7
    assert comparison.loc['M2', 'state_nrmse_mean'] < comparison.loc['M0', 'state_nrmse_mean']
    assert comparison.loc['M2', 'absolute_risk_discrepancy_mean'] < comparison.loc['M0', 'absolute_risk_discrepancy_mean']


def test_rq1_is_54_distinct_decisions_and_paired_speedup_is_a_ratio():
    paired = pd.read_parquet(GOC / 'rq1/tables/rq1_paired_runtime.parquet')
    assert len(paired) == paired.decision_sha256.nunique() == 54
    np.testing.assert_allclose(paired.evaluator_speedup,
        paired.refa_evaluator_median_seconds / paired.m0_evaluator_median_seconds, rtol=1e-12)
    summary = json.loads((GOC / 'rq1/rq1_runtime_summary.json').read_text())
    assert np.isclose(summary['paired_speedup']['evaluator_median'], paired.evaluator_speedup.median())
    warm = pd.read_parquet(GOC / 'refined_study/core_results/warm_start_crossed.parquet')
    assert len(warm) == 525
    assert warm.groupby('warm_start_type').size().eq(75).all()


def test_texas_coverage_never_imputes_missing_native_results_or_residuals():
    coverage = study_coverage(ROOT)
    assert coverage['texas2k']['certified_fit_rows'] == 8
    assert coverage['texas2k']['validation_rows'] == 2100
    assert coverage['texas2k']['locally_retained_validation_checkpoints'] == 7
    assert coverage['texas2k']['completed_native_searches'] == 0
    validation = texas_validation(ROOT)
    assert not validation.checkpoint_task.eq('v070.opengridsfm.G500.s0.validation').any()
    assert validation.loc[validation.family.eq('opengridsfm'), 'metric_source'].eq('independent physical audit').all()


def test_historical_plot_recovers_k_l_service_fields_from_their_actual_a_b_tables():
    comparison = texas_historical_comparison(ROOT)
    assert comparison.selected_service.notna().all()
    dc = comparison.loc[comparison.stage.eq('K') & comparison.model.eq('dc')].iloc[0]
    ac = comparison.loc[comparison.stage.eq('K') & comparison.model.eq('ac')].iloc[0]
    assert np.isclose(dc.selected_service, .56238, atol=1e-5)
    assert np.isclose(ac.selected_service, .65391, atol=1e-5)
    assert dc.b_r > 1 and ac.b_r > 1
    assert dc.maximum_service_fraction > .99999 and ac.maximum_service_fraction > .99999
