"""Fresh bounded GOC-500 surrogate OPS, distinct from published full searches."""

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import time

import numpy as np
from scipy.optimize import minimize
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

from .artifacts import checked_path, sha
from .demo_physics import (
    SOURCE_SHA256, build_goc500_identity, compute_ac_loading_two_ended,
    compute_j_trade, compute_r_base, mutate_raw_case_for_candidate,
    require_valid_risk_ratings,
)


DEMO_ID = 'GOC500_SAMPLE_BOUNDED_ALPHA_POWELL_DEMO_V1'


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def load_demo_config(path):
    config = json.loads(Path(path).read_text())
    if config.get('demo_id') != DEMO_ID:
        raise ValueError('an explicitly distinct bounded demo configuration is required')
    budget, controls = config.get('max_calls_per_topology'), config.get('control_load_count')
    if type(budget) is not int or not 2 <= budget <= 20:
        raise ValueError('demo requires two to twenty actual calls per topology')
    if type(controls) is not int or not 1 <= controls <= 5:
        raise ValueError('demo supports one to five per-load alpha controls')
    weight = config.get('lambda_r')
    if type(weight) not in (int, float) or not np.isfinite(weight) or not 0 <= weight <= 1:
        raise ValueError('lambda_r must be finite and in [0, 1]')
    if config.get('hazard_policy') != 'SYNTHETIC_UNIFORM_NOT_GEOGRAPHIC':
        raise ValueError('the sample demo has no calibrated geographic hazard')
    branch = config.get('offline_branch_id')
    if branch is not None and type(branch) is not int:
        raise ValueError('offline_branch_id must be an original physical integer ID')
    return config


def load_published_config(path, expected_sha256):
    """Inspect an independently supplied full configuration without executing it."""
    if sha(path) != expected_sha256:
        raise ValueError('published configuration checksum differs')
    config = json.loads(Path(path).read_text())
    if not isinstance(config, dict) or not config or 'demo_id' in config:
        raise ValueError('a full published configuration must be separate from the demo')
    return dict(status='CONFIG_LOADED_ONLY_NOT_RECOMPUTED', config=config,
                sha256=expected_sha256, numerical_execution=False,
                published_full_search_recomputed=False)


def _connected(identity, offline):
    index = {bus: i for i, bus in enumerate(identity.bus_ids)}
    edges = [(index[b.from_bus_id], index[b.to_bus_id]) for b in identity.branches
             if b.canonical_branch_id not in offline]
    rows, cols = zip(*edges)
    adjacency = csr_matrix((np.ones(len(edges)), (rows, cols)),
                           shape=(len(index), len(index)))
    return connected_components(adjacency, directed=False, return_labels=False) == 1


def _outage(identity, requested):
    risk_ids = sorted(b.canonical_branch_id for b in identity.branches if b.is_risk)
    candidates = risk_ids if requested is None else [requested]
    for branch in candidates:
        if branch not in risk_ids:
            raise ValueError('outage must identify an existing physical AC line')
        if _connected(identity, {branch}):
            return branch
    raise ValueError('no connected single-line demo outage is available')


def _flow_maps(output, identity):
    families = [('ac_line', [b for b in identity.branches if b.edge_family == 'ac_line']),
                ('transformer', [b for b in identity.branches if b.edge_family == 'transformer'])]
    families = [(name, branches) for name, branches in families if branches]
    if (list(output['flow_edge_types']) != [name for name, _ in families]
            or list(output['flow_edge_counts']) != [len(rows) for _, rows in families]):
        raise ValueError('official flow family ordering/counts do not match physical IDs')
    ids = [b.canonical_branch_id for _, branches in families for b in branches]
    maps = []
    for name in ('Pij', 'Qij', 'Pji', 'Qji'):
        value = output[name]
        values = np.asarray(value.detach().cpu() if hasattr(value, 'detach') else value).reshape(-1)
        if len(values) != len(ids) or not np.isfinite(values).all():
            raise ValueError('nonfinite or incomplete official branch flows')
        maps.append(dict(zip(ids, map(float, values))))
    return maps


def _baseline(raw, identity):
    baseline = {}
    for branch in identity.branches:
        if not branch.is_risk:
            continue
        row = raw['solution']['edges'][branch.edge_family]['features'][branch.family_index]
        if len(row) != 4 or not np.isfinite(row).all():
            raise ValueError('sample baseline requires finite saved two-ended AC flows')
        baseline[branch.canonical_branch_id] = max(np.hypot(*row[:2]), np.hypot(*row[2:])) / branch.rate_a
    return baseline


def _evaluate(raw, identity, model, offline, alpha, hazard, r_base, lambda_r, predict=None):
    import gridsfm
    # Inference reads only grid/metadata; avoid carrying stale solution labels
    # through topology mutation (the official sample has dictionary edge blocks).
    inference_raw = {key: value for key, value in raw.items() if key != 'solution'}
    mutated, shedding, integrity = mutate_raw_case_for_candidate(
        inference_raw, identity, offline_branch_ids=offline, alpha_requested=alpha)
    with TemporaryDirectory(prefix='goc500-candidate-') as temporary:
        path = Path(temporary) / 'candidate.pyg.json'
        path.write_text(json.dumps(mutated, allow_nan=False))
        output = (predict or gridsfm.predict)(model, path, fmt='pyg')
    active = build_goc500_identity(mutated)
    flows = _flow_maps(output, active)
    risk_ids = [b.canonical_branch_id for b in active.branches if b.is_risk]
    ratings = {b.canonical_branch_id: b.rate_a for b in active.branches}
    loading = compute_ac_loading_two_ended(*flows, ratings, risk_ids)
    risk = sum(hazard[line] * loading[line] ** 2 for line in risk_ids) / r_base
    objective = compute_j_trade(lambda_r, risk, shedding.l_shed_total)
    predictions = {}
    for key in ('theta', 'V', 'Pg', 'Qg'):
        values = output[key].detach().cpu().numpy()
        if not np.isfinite(values).all():
            raise ValueError('nonfinite official node prediction')
        predictions[key] = values.tolist()
    return dict(r_norm=risk, l_shed_total=shedding.l_shed_total,
                l_shed_control=shedding.l_shed_control, l_shed_island=shedding.l_shed_island,
                j_trade=objective, search_objective=objective,
                alpha_requested=shedding.alpha_requested, alpha_effective=shedding.alpha_effective,
                source_less_load_ids=list(shedding.source_less_load_ids), d_input=integrity.d_input,
                feasibility_head=float(output['feas']), ac_feasibility_certified=False,
                branches=[dict(canonical_branch_id=line, rate_a=ratings[line],
                               p_from=flows[0][line], q_from=flows[1][line],
                               p_to=flows[2][line], q_to=flows[3][line], physical_loading=loading[line])
                          for line in risk_ids], predictions=predictions)


class _BudgetExhausted(Exception):
    pass


def search_topology(evaluate, load_ids, control_ids, budget, model_call_count=None):
    """Count every evaluator invocation; SciPy proposals never exceed the cap."""
    if type(budget) is not int or not 2 <= budget <= 20:
        raise ValueError('actual evaluation budget must be two to twenty')
    trace, best = [], None

    def objective(x):
        nonlocal best
        if len(trace) >= budget:
            raise _BudgetExhausted
        if not np.isfinite(x).all() or np.any(np.asarray(x) < 0) or np.any(np.asarray(x) > 1):
            raise ValueError('optimizer alpha proposal escaped [0, 1]')
        alpha = dict.fromkeys(load_ids, 1.0)
        alpha.update(zip(control_ids, map(float, x)))
        row = dict(evaluation_index=len(trace) + 1, alpha_requested=alpha,
                   optimizer_coordinates=list(map(float, x)))
        trace.append(row)
        before_calls = model_call_count() if model_call_count else None
        started = time.perf_counter()
        try:
            value = evaluate(alpha)
            merit = float(value['search_objective'])
            if not np.isfinite(merit):
                raise ValueError('nonfinite candidate merit')
        except Exception as exc:
            row.update(status='FAILED_EVALUATION', error=str(exc), search_objective=None)
            return 1e100
        finally:
            row['elapsed_seconds'] = time.perf_counter() - started
            if model_call_count:
                row['model_called'] = model_call_count() > before_calls
        row.update(status='FINITE_SURROGATE_NOT_AC_CERTIFICATE', search_objective=merit,
                   r_norm=value['r_norm'], l_shed_total=value['l_shed_total'],
                   alpha_effective=value['alpha_effective'])
        if best is None or merit < best['search_objective']:
            best = dict(value, evaluation_index=row['evaluation_index'])
        return merit

    objective(np.ones(len(control_ids)))
    objective(np.full(len(control_ids), .9))
    if budget > 2:
        try:
            minimize(objective, np.full(len(control_ids), .9), method='Powell',
                     bounds=[(0.0, 1.0)] * len(control_ids),
                     options=dict(maxfev=budget - len(trace), maxiter=budget, xtol=1e-3, ftol=1e-6))
        except _BudgetExhausted:
            pass
    if best is None:
        raise ValueError('no finite numerical candidate; demo is not certified')
    return dict(best=best, actual_calls=len(trace), max_calls=budget, trace=trace)


def run_demo(root, model_id, output, config_path=None):
    import gridsfm
    import torch
    root, output = Path(root).resolve(), Path(output).resolve()
    config_path = Path(config_path) if config_path else root / 'experiments/goc_500/demo_config.json'
    config = load_demo_config(config_path)
    catalog = json.loads((root / 'artifacts/model_catalog.json').read_text())['models']
    if model_id not in catalog or not model_id.startswith('goc500.'):
        raise ValueError('demo requires a catalogued GOC500 model')
    spec = catalog[model_id]
    if spec['family'] != 'opengridsfm':
        raise ValueError('GOC500 demo requires the official native GridSFM interface')
    checkpoint, fixture = checked_path(root, spec['weights']), checked_path(root, spec['demo_input'])
    if sha(checkpoint) != spec['sha256'] or sha(fixture) != spec['demo_input_sha256']:
        raise ValueError('checkpoint or official sample checksum differs from catalog')
    # Never write into source evidence/model caches, even for a mistaken CLI path.
    if output == root or any(output.is_relative_to(root / name) for name in ('src', 'artifacts', 'experiments')):
        raise ValueError('demo output must be separate from packaged code, evidence and models')
    if (output / 'demo_result.json').exists():
        raise ValueError('preserve the existing demo result; choose a fresh output')
    raw = json.loads(fixture.read_text())
    identity = build_goc500_identity(raw)
    physical_ids = [b.canonical_branch_id for b in identity.branches]
    if len(set(physical_ids)) != len(physical_ids):
        raise ValueError('physical branch IDs must be unique across edge families')
    require_valid_risk_ratings(identity)
    offline = _outage(identity, config.get('offline_branch_id'))
    hazard = {b.canonical_branch_id: 1.0 for b in identity.branches if b.is_risk}
    baseline = _baseline(raw, identity)
    r_base = compute_r_base(hazard, baseline, hazard)
    positive_loads = sorted((load for load in identity.loads if load.pd_pre > 0),
                            key=lambda load: (-load.pd_pre, load.canonical_load_id))
    controls = [load.canonical_load_id for load in positive_loads[:config['control_load_count']]]
    if len(controls) != config['control_load_count']:
        raise ValueError('not enough positive-demand loads for requested alpha controls')
    torch.set_num_threads(2)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    model = gridsfm.load_model(checkpoint, device='cpu')
    model.eval()
    model_calls = 0

    def predict(*args, **kwargs):
        nonlocal model_calls
        model_calls += 1
        return gridsfm.predict(*args, **kwargs)

    topology_results = []
    for outages in ([], [offline]):
        before_calls = model_calls
        result = search_topology(
            lambda alpha: _evaluate(raw, identity, model, outages, alpha, hazard, r_base, config['lambda_r'], predict),
            [load.canonical_load_id for load in identity.loads], controls,
            config['max_calls_per_topology'], lambda: model_calls)
        topology_results.append(dict(offline_branch_ids=outages, actual_model_calls=model_calls-before_calls, **result))
    if sha(fixture) != spec['demo_input_sha256'] or sha(checkpoint) != spec['sha256']:
        raise ValueError('source sample or checkpoint changed during the demo')
    selected = min(topology_results, key=lambda item: item['best']['search_objective'])
    result = dict(status='PASS_BOUNDED_SURROGATE_DEMO_NOT_AC_FEASIBILITY', demo_id=DEMO_ID,
                  run_identity_sha256=_digest(dict(config=config, model_id=model_id,
                      checkpoint_sha256=spec['sha256'], input_sha256=spec['demo_input_sha256'])),
                  model_id=model_id, checkpoint_sha256=spec['sha256'], input_sha256=spec['demo_input_sha256'],
                  config=config, config_sha256=sha(config_path), device='cpu', torch=torch.__version__,
                  physical_branch_id_policy='ORIGINAL_METADATA_IDS_NOT_PREPARED_OR_REVERSE_EDGE_ROWS',
                  normalization='OFFICIAL_GRIDSFM_V1_1_UNCHANGED_NATIVE_FLOW_AND_RATING_UNITS',
                  hazard_policy=config['hazard_policy'], calibrated_geographic_wildfire_claim=False,
                  baseline_policy='SAVED_OFFICIAL_SAMPLE_AC_SOLUTION_NOT_PUBLISHED_STAGE_J_BASELINE',
                  r_base=r_base, baseline_loading=baseline, p_env=hazard,
                  selection_objective='J_TRADE_ONLY_DEMO_NO_CALIBRATED_PAC_WEIGHTS',
                  alpha_policy='LARGEST_POSITIVE_LOADS_PER_LOAD_CONTROLS_OTHER_REQUESTS_ONE',
                  control_load_ids=controls, optimizer='SCIPY_BOUNDED_POWELL_WITH_TWO_SEEDS',
                  stage_j_portable_source_sha256=SOURCE_SHA256,
                  actual_model_calls=model_calls,
                  topology_count=len(topology_results), topologies=topology_results,
                  selected_offline_branch_ids=selected['offline_branch_ids'],
                  published_production_result=False, published_full_search_recomputed=False,
                  cached_replay=False, ac_audit_executed=False, ac_feasibility_certified=False)
    output.mkdir(parents=True, exist_ok=True)
    destination = output / 'demo_result.json'
    with destination.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    return dict(status=result['status'], demo_id=DEMO_ID, model_id=model_id,
                result=str(destination), actual_model_calls=result['actual_model_calls'],
                topology_count=2, published_full_search_recomputed=False, ac_audit_executed=False)
