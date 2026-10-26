"""Public workflow contracts: grid identity, truthful readiness and safe dispatch."""

import hashlib
import json
from pathlib import Path

import pytest

from genco_ops.catalog import format_models, model_spec, models, saved_case_path
from genco_ops.inference import predict_saved_case
from genco_ops.workflow import run_public_genco, run_workflow, validate_output


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def release(tmp_path):
    root = tmp_path / 'repo'
    (root / 'artifacts').mkdir(parents=True)
    digest = lambda value: hashlib.sha256(value).hexdigest()
    spec = dict(family='opengridsfm', weights='artifacts/cache/model.pt', sha256=digest(b'weights'),
                demo_input='artifacts/private_inputs/graph.pt', demo_input_sha256=digest(b'case'),
                scientific_certification='PASS', ops='PENDING')
    (root / 'artifacts/model_catalog.json').write_text(json.dumps(dict(models={
        'texas2k.opengridsfm.G500': spec, 'goc500.base': spec})))
    (root / 'artifacts/cache').mkdir()
    (root / spec['weights']).write_bytes(b'weights')
    return root


def test_catalog_grid_roles_and_readiness_do_not_claim_population_reproduction():
    rows = models(ROOT)
    assert len(rows) >= 15
    assert next(row for row in rows if row['model_id'] == 'goc500.ft0')['role'] == 'smoke'
    assert next(row for row in rows if row['model_id'] == 'texas2k.genco_opf.G100')['role'] == 'intermediate'
    assert next(row for row in rows if row['model_id'] == 'goc500.base')['role'] == 'base'
    assert all(row['study'] == 'goc_500' for row in models(ROOT, 'goc500'))
    assert 'published' not in next(row for row in rows if row['model_id'] == 'goc500.m2')['supported_modes']
    assert 'saved_case_ready' in rows[0]
    assert all(asset['verified'] is None for row in rows for asset in row['assets'].values())
    assert 'published-population' in format_models(rows)


def test_cross_grid_model_cannot_enter_execution(release, monkeypatch):
    monkeypatch.setattr('genco_ops.inference.predict_saved_case', lambda *a, **k: pytest.fail('no inference'))
    with pytest.raises(ValueError, match='belongs to texas2k'):
        run_workflow(release, 'goc_500', 'texas2k.opengridsfm.G500', release / 'outputs/run', execute=True)
    assert not (release / 'outputs').exists()


def test_file_presence_is_distinct_from_hash_validation(release):
    row = models(release, 'texas2k')[0]
    assert row['weights_ready'] is True and row['saved_case_ready'] is False
    assert row['assets']['weights']['verified'] is None
    (release / row['assets']['weights']['path']).write_bytes(b'changed')
    row = models(release, 'texas2k', verify_hashes=True)[0]
    assert row['weights_ready'] is False
    assert row['assets']['weights']['verified'] is False


def test_missing_saved_case_plan_does_no_numerical_work_or_output_mutation(release, monkeypatch):
    monkeypatch.setattr('genco_ops.inference.predict_saved_case', lambda *a, **k: pytest.fail('no inference'))
    result = run_workflow(release, 'texas2k', 'texas2k.opengridsfm.G500', release / 'outputs/run')
    assert result['status'] == 'MISSING_ARTIFACTS'
    assert result['numerical_execution'] is False
    assert result['missing_assets'] == ['artifacts/private_inputs/graph.pt']
    assert not (release / 'outputs').exists()
    with pytest.raises(ValueError, match='MISSING_ARTIFACTS'):
        run_workflow(release, 'texas2k', 'texas2k.opengridsfm.G500', release / 'outputs/run', execute=True)


@pytest.mark.parametrize('layout', ['file', 'basename', 'tree'])
def test_authorized_external_graph_pack_retains_catalog_checksum(release, tmp_path, monkeypatch, layout):
    spec, _ = model_spec(release, 'texas2k.opengridsfm.G500')
    pack = tmp_path / 'authorized'
    case = pack / (spec['demo_input'] if layout == 'tree' else Path(spec['demo_input']).name)
    case.parent.mkdir(parents=True)
    case.write_bytes(b'case')
    inputs = case if layout == 'file' else pack
    assert saved_case_path(release, spec, inputs) == case
    observed = []
    monkeypatch.setattr('genco_ops.inference.predict_saved_case',
                        lambda *a, **k: observed.append((a, k)) or {'status': 'ACTUAL_ADAPTER'})
    result = run_workflow(release, 'texas2k', 'texas2k.opengridsfm.G500',
                          release / 'outputs/run', inputs=inputs, execute=True)
    assert result['status'] == 'ACTUAL_ADAPTER'
    assert observed[0][1]['inputs'] == inputs
    case.write_bytes(b'not the certified case')
    with pytest.raises(ValueError, match='CHECKSUM_MISMATCH'):
        run_workflow(release, 'texas2k', 'texas2k.opengridsfm.G500',
                     release / 'outputs/other', inputs=inputs, execute=True)
    assert len(observed) == 1


@pytest.mark.parametrize('directory', ['', 'src/run', 'artifacts/cache/run', 'experiments/run',
                                      'notebooks/run', '.git/run', 'dist/run'])
def test_cannot_write_numerical_outputs_over_packaged_content(release, directory):
    with pytest.raises(ValueError, match='separate from packaged'):
        validate_output(release, release / directory)
    assert validate_output(release, release / 'outputs/run') == release / 'outputs/run'


def test_existing_prediction_is_preserved_before_loading_model(release):
    output = release / 'outputs/already-run'
    output.mkdir(parents=True)
    (output / 'prediction.pt').write_bytes(b'preserved')
    with pytest.raises(ValueError, match='preserve the existing prediction'):
        predict_saved_case(release, 'texas2k.opengridsfm.G500', output)
    assert (output / 'prediction.pt').read_bytes() == b'preserved'


def test_goc_demo_plan_keeps_distinct_budget_and_refuses_full_population_claim(tmp_path):
    result = run_workflow(ROOT, 'goc_500', 'goc500.m2', tmp_path / 'demo', mode='demo')
    assert result['scope'] == 'OFFICIAL_SAMPLE_DEMO_NOT_PUBLISHED_GOC_POPULATION'
    assert result['topology_count'] == 2 and result['maximum_model_calls'] <= 40
    assert result['published_full_search_recomputed'] is False
    with pytest.raises(ValueError, match='historical GOC full-search input population'):
        run_workflow(ROOT, 'goc_500', 'goc500.m2', tmp_path / 'full', mode='published')


def test_texas_full_plan_advertises_original_budget_and_requires_actual_inputs(release):
    result = run_workflow(release, 'texas2k', 'texas2k.opengridsfm.G500',
                          release / 'outputs/published', mode='published')
    assert result['maximum_topology_count'] == 301
    assert result['maximum_model_calls'] == 6020
    assert result['device'] == 'cuda:0'
    assert result['status'] == 'INPUTS_REQUIRED'
    assert result['numerical_execution'] is False
    assert result['missing_assets'] == []  # saved-case graph is not used by prepared OPS adapter
    assert not (release / 'outputs').exists()


def test_public_genco_plan_uses_the_base_and_preserves_texas_population_identity(tmp_path, monkeypatch):
    monkeypatch.setattr('genco_ops.public_genco_demo.run_public_demo',
                        lambda *a, **k: pytest.fail('plan cannot run a model'))
    result = run_public_genco(ROOT, tmp_path / 'public-demo')
    assert result['model_id'] == 'texas2k.genco_opf.base'
    assert result['input_grid'] == 'PUBLIC_IEEE14'
    assert result['texas2k_result'] is False
    assert result['fine_tuning_benefit_established'] is False
    assert result['maximum_model_calls'] == 1
    assert result['numerical_execution'] is False
    assert not (tmp_path / 'public-demo').exists()
