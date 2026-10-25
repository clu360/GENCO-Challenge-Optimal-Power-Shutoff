import ast
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pytest

from genco_ops.artifacts import sha
from genco_ops import demo_physics as physics
from genco_ops.goc500_demo import (
    DEMO_ID, _baseline, _flow_maps, _outage, load_demo_config,
    load_published_config, run_demo, search_topology,
)


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / 'experiments/goc_500/data/case500_goc.pyg.json'


def test_portable_modules_have_no_research_imports_or_path_changes():
    for name in ('demo_physics.py', 'goc500_demo.py'):
        tree = ast.parse((ROOT / 'src/genco_ops' / name).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or '').startswith('experiments')
            if isinstance(node, ast.Import):
                assert not any(alias.name.startswith('experiments') for alias in node.names)
        assert 'sys.path' not in ast.unparse(tree)


def test_outage_preserves_physical_ids_and_original_sample():
    raw = json.loads(SAMPLE.read_text())
    before = deepcopy(raw)
    identity = physics.build_goc500_identity(raw)
    outage = _outage(identity, None)
    alpha = {load.canonical_load_id: .8 for load in identity.loads}
    inference = {key: value for key, value in raw.items() if key != 'solution'}
    mutated, shedding, report = physics.mutate_raw_case_for_candidate(
        inference, identity, offline_branch_ids=[outage], alpha_requested=alpha)
    active = physics.build_goc500_identity(mutated)
    expected = [b.canonical_branch_id for b in identity.branches if b.canonical_branch_id != outage]
    assert [b.canonical_branch_id for b in active.branches] == expected
    assert all(b.rate_a == identity.branch_by_id[b.canonical_branch_id].rate_a for b in active.branches)
    assert shedding.l_shed_total == pytest.approx(.2)
    assert shedding.l_shed_island == 0
    assert report.d_input == 0
    assert raw == before
    assert physics.SOURCE_SHA256.keys() == {'schemas.py', 'contracts.py', 'load_service.py', 'goc500_adapter.py', 'metrics.py'}


def test_source_less_island_enforces_zero_load_and_separate_shedding():
    raw = dict(grid=dict(nodes=dict(bus=[[0, 0, .9, 1.1]] * 2,
        generator=[[0, 0, 0, 1]], load=[[1., .3]]), edges=dict(
        ac_line=dict(senders=[0], receivers=[1], features=[[0, 0, 0, 0, .01, .1, 2.]]),
        load_link=dict(senders=[0], receivers=[1]))), metadata=dict(
        bus_id_map=[10, 20], gen_bus_map=[10], load_bus_map=[20],
        load_id_map=[7], ac_line_branch_ids=[101]))
    identity = physics.build_goc500_identity(raw)
    mutated, shed, integrity = physics.mutate_raw_case_for_candidate(
        raw, identity, offline_branch_ids=[101], alpha_requested={7: .8})
    assert shed.alpha_requested == {7: .8}
    assert shed.alpha_effective == {7: 0.}
    assert shed.l_shed_island == 1. and shed.l_shed_control == 0.
    assert mutated['grid']['nodes']['load'] == [[0., 0.]]
    assert integrity.d_input == 0


def test_two_ended_loading_and_sample_baseline_use_same_native_units():
    loading = physics.compute_ac_loading_two_ended({101: 3.}, {101: 4.}, {101: 6.}, {101: 8.}, {101: 2.}, [101])
    assert loading == {101: 5.}
    assert physics.compute_r_base({101: .4}, loading, [101]) == 10.
    assert physics.compute_j_trade(.8, .5, .2) == pytest.approx(.44)
    raw = json.loads(SAMPLE.read_text())
    identity = physics.build_goc500_identity(raw)
    baseline = _baseline(raw, identity)
    branch = next(b for b in identity.branches if b.is_risk)
    row = raw['solution']['edges'][branch.edge_family]['features'][branch.family_index]
    assert baseline[branch.canonical_branch_id] == pytest.approx(max(np.hypot(*row[:2]), np.hypot(*row[2:])) / branch.rate_a)


def test_flow_family_and_count_mismatch_cannot_relabel_branch_ids():
    raw = json.loads(SAMPLE.read_text())
    identity = physics.build_goc500_identity(raw)
    with pytest.raises(ValueError, match='ordering/counts'):
        _flow_maps(dict(flow_edge_types=['transformer', 'ac_line'], flow_edge_counts=[1, 1]), identity)


@pytest.mark.parametrize('budget', [2, 8, 20])
def test_actual_evaluation_cap_and_full_per_load_alpha(budget):
    calls = []

    def evaluate(alpha):
        calls.append(alpha)
        assert set(alpha) == {7, 19, 31}
        assert alpha[31] == 1.
        assert all(0 <= value <= 1 for value in alpha.values())
        risk = sum(value ** 2 for value in alpha.values())
        shed = 1 - sum(alpha.values()) / len(alpha)
        return dict(search_objective=.8*risk+.2*shed, r_norm=risk,
                    l_shed_total=shed, alpha_effective=alpha)

    result = search_topology(evaluate, [7, 19, 31], [7, 19], budget)
    assert 2 <= len(calls) == result['actual_calls'] <= budget
    assert result['best']['search_objective'] == min(row['search_objective'] for row in result['trace'])
    assert calls[0] == {7: 1., 19: 1., 31: 1.}
    assert calls[1] == {7: .9, 19: .9, 31: 1.}


def test_failed_evaluations_consume_budget_and_never_certify():
    calls = []

    def failed(alpha):
        calls.append(alpha)
        raise RuntimeError('no model output')

    with pytest.raises(ValueError, match='no finite'):
        search_topology(failed, [7], [7], 4)
    assert len(calls) <= 4


@pytest.mark.parametrize('budget', [True, 0, 1, 21, 1.5])
def test_demo_rejects_unbounded_or_noninteger_budget(tmp_path, budget):
    config = json.loads((ROOT / 'experiments/goc_500/demo_config.json').read_text())
    config['max_calls_per_topology'] = budget
    path = tmp_path / 'config.json'
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match='twenty actual'):
        load_demo_config(path)


def test_published_config_load_is_separate_and_executes_nothing(tmp_path):
    path = tmp_path / 'published.json'
    path.write_text(json.dumps(dict(artifact_id='ORIGINAL_FULL_SEARCH', topology_budget=301)))
    result = load_published_config(path, sha(path))
    assert result['numerical_execution'] is False
    assert result['published_full_search_recomputed'] is False
    with pytest.raises(ValueError, match='separate'):
        load_published_config(ROOT / 'experiments/goc_500/demo_config.json',
                              sha(ROOT / 'experiments/goc_500/demo_config.json'))


@pytest.mark.parametrize('model_id', ['goc500.base', 'goc500.m1'])
def test_real_cpu_demo_evaluates_changed_grid_and_alpha(tmp_path, model_id):
    pytest.importorskip('gridsfm')
    catalog = json.loads((ROOT / 'artifacts/model_catalog.json').read_text())['models']
    if not (ROOT / catalog[model_id]['weights']).exists():
        pytest.skip('acquired checksum-bound model bundle is required for numerical test')
    config = json.loads((ROOT / 'experiments/goc_500/demo_config.json').read_text())
    config['max_calls_per_topology'] = 4
    path = tmp_path / 'demo_config.json'
    path.write_text(json.dumps(config))
    result = run_demo(ROOT, model_id, tmp_path / model_id, path)
    data = json.loads(Path(result['result']).read_text())
    assert data['demo_id'] == DEMO_ID
    assert data['actual_model_calls'] == 8
    assert data['cached_replay'] is False
    assert data['published_full_search_recomputed'] is False
    assert data['calibrated_geographic_wildfire_claim'] is False
    assert data['ac_feasibility_certified'] is False
    assert data['topologies'][0]['offline_branch_ids'] == []
    for topology in data['topologies']:
        assert topology['actual_model_calls'] == topology['actual_calls'] == 4
        assert all(row['model_called'] for row in topology['trace'])
        assert all(row['status'] == 'FINITE_SURROGATE_NOT_AC_CERTIFICATE' for row in topology['trace'])
        best = topology['best']
        reconstructed = sum(row['physical_loading'] ** 2 for row in best['branches']) / data['r_base']
        assert best['r_norm'] == pytest.approx(reconstructed)
        assert best['j_trade'] == pytest.approx(.8 * reconstructed + .2 * best['l_shed_total'])
        assert not set(topology['offline_branch_ids']) & {row['canonical_branch_id'] for row in best['branches']}
        assert len(best['alpha_effective']) == 281
    intact, outage = data['topologies']
    assert len(intact['best']['branches']) == len(outage['best']['branches']) + 1
    assert intact['trace'][0]['r_norm'] != pytest.approx(intact['trace'][1]['r_norm'], abs=1e-10)
