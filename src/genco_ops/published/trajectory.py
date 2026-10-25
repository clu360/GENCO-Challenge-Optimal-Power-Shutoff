
"""Restartable Stage M outer search using the established Stage K/L topology rules."""
from dataclasses import asdict
import json
import math
from pathlib import Path
import pandas as pd
from .selection import select_finalist
from .schemas import CandidateResult
from .topology import k2_children, topology_key
from .rows import _candidate_row, _plain
from .io import atomic_json
from ..artifacts import sha
from .search import PF_SEARCH_ID, ALPHA_SEARCH_ID

def _ids(value):
    return () if not value or value == 'intact' else tuple(sorted(map(int, value.split(';'))))

def validate_candidate(result, trace, offline, search_id, output, *, payload_store=None, request_sha256=None):
    if tuple(_ids(result.offline_branch_ids)) != offline or result.k != len(offline) or result.topology_key != topology_key(offline) or (result.metadata.get('search_id') != search_id):
        raise ValueError('candidate topology/search contract mismatch')
    blocks = result.metadata.get('search_blocks', [])
    expected = [('r', 10), ('alpha', 10)] if search_id == PF_SEARCH_ID else [('alpha', 20)]
    actual_blocks = [(b['block'], b['budget']) for b in blocks]
    valid_blocks = actual_blocks == expected or (not result.eligible and search_id == PF_SEARCH_ID and (actual_blocks == expected[:1]))
    if not valid_blocks or any((not 0 <= b['actual_evaluations'] <= b['budget'] for b in blocks)) or sum((b['actual_evaluations'] for b in blocks)) != len(trace) or (len(trace) > 20):
        raise ValueError('candidate actual objective-evaluation budget mismatch')
    expected_trace = [b['block'] for b in blocks for _ in range(b['actual_evaluations'])]
    if [r.get('block') for r in trace] != expected_trace or [r.get('evaluation_index') for r in trace] != list(range(1, len(trace) + 1)):
        raise ValueError('actual OPS trace block order/count differs from declared budget')
    for block in blocks:
        indices = [r.get('block_evaluation_index') for r in trace if r.get('block') == block['block']]
        if indices != list(range(1, block['actual_evaluations'] + 1)):
            raise ValueError('actual per-block objective-call indices differ')
    if result.eligible and (result.search_objective is None or not math.isfinite(result.search_objective)):
        raise ValueError('eligible OPS objective must be finite')
    artifacts = result.metadata.get('state_artifacts', {})
    if result.eligible and (not artifacts):
        raise ValueError('eligible OPS candidate requires physical state artifacts')
    if result.eligible:
        state = (output / 'state' / result.topology_key.replace(';', '_')).resolve()
        if not result.state_path or Path(result.state_path).resolve() != state or (not state.is_relative_to(output)):
            raise ValueError('eligible reference state directory differs from candidate topology')
        required = ('bus_state.parquet', 'branch_state.parquet', 'generator_state.parquet', 'load_service.parquet')
        if any(((state / name).relative_to(output).as_posix() not in artifacts for name in required)):
            raise ValueError('reference-consumed state tables are not hash-bound')
    for name, expected_hash in (artifacts | result.metadata.get('call_artifacts', {})).items():
        path = (output / name).resolve()
        if not path.is_relative_to(output) or sha(path) != expected_hash:
            raise ValueError('OPS physical state artifact changed')
    database = result.metadata.get('payload_database')
    if database is not None or (payload_store is not None and trace):
        if payload_store is None or database != str(payload_store.path):
            raise ValueError('candidate packed payload database is not request-bound')
        path = output / 'call_journals' / result.topology_key.replace(';', '_') / 'ledger.json'
        if result.metadata.get('call_artifacts', {}).get(path.relative_to(output).as_posix()) != sha(path):
            raise ValueError('packed journal requires its candidate-bound ledger')
        ledger = json.loads(path.read_text())
        identity = ledger['identity']
        if identity['request_sha256'] != request_sha256 or identity['topology'] != list(offline) or identity['lambda_r'] != result.lambda_r or (len(ledger['calls']) != len(trace)):
            raise ValueError('packed journal scientific identity or call count changed')
        for index, call in enumerate(ledger['calls'], 1):
            if call['status'] != 'COMPLETE' or call['actual_call_index'] != index:
                raise ValueError('packed journal contains an uncertain or reordered call')
            payload_store.read(identity, call['key'], call['sha256'])

def _run_trajectory(*, resident, identity, prepared_dir, output, model_key, lambda_r, search_config, request_sha256, search_id):
    """The resident owns checkpoint inference and unchanged physical/objective metrics.

    Config and all input/source/checkpoint hashes must be bound by request_sha256
    in the enclosing executor. No released-checkpoint registry is mutated.
    """
    if search_id not in (PF_SEARCH_ID, ALPHA_SEARCH_ID):
        raise ValueError('only the approved Stage M sequential search is supported')
    if not isinstance(request_sha256, str) or len(request_sha256) != 64:
        raise ValueError('immutable complete OPS request identity required')
    if search_config['continuous_budget'] != 20:
        raise ValueError('Stage M continuous budget must remain twenty actual calls')
    output, prepared_dir = (Path(output).resolve(), Path(prepared_dir).resolve())
    output.mkdir(parents=True, exist_ok=True)
    identity_file = output / 'trajectory_identity.json'
    expected_identity = dict(request_sha256=request_sha256, evaluator=model_key, lambda_r=lambda_r, search_id=search_id)
    if identity_file.exists():
        if json.loads(identity_file.read_text()) != expected_identity:
            raise ValueError('OPS trajectory identity changed')
    else:
        if any(output.iterdir()):
            raise ValueError('refuse to adopt or overwrite an unowned result directory')
        atomic_json(identity_file, expected_identity)
    proxy = pd.read_parquet(prepared_dir / 'proxy_components.parquet')
    shared = pd.read_parquet(prepared_dir / 'shared_k1.parquet')
    chosen = shared.loc[shared.lambda_r.astype(float).eq(lambda_r)]
    k1 = [_ids(r.offline_branch_ids) for r in chosen.itertuples(index=False)]
    if len(k1) != search_config['k1_count'] or len(set(k1)) != len(k1) or any((len(z) != 1 or z[0] not in identity.l_trans for z in k1)):
        raise ValueError('shared K1 input is empty, duplicated or outside switchable lines')
    if any((type(search_config[k]) is not int or search_config[k] <= 0 for k in ('k1_count', 'parent_count', 'k2_children_per_parent', 'k2_max_unique'))) or search_config['k2_max_unique'] > search_config['parent_count'] * search_config['k2_children_per_parent']:
        raise ValueError('invalid frozen outer-search budget')
    weights = dict(zip(proxy.canonical_branch_id.astype(int), proxy.weight.astype(float), strict=True))
    costs = dict(zip(proxy.canonical_branch_id.astype(int), proxy.c_l.astype(float), strict=True))
    rows, continuous = ([], [])
    checkpoints = output / 'checkpoints'
    checkpoints.mkdir(exist_ok=True)

    def one(offline):
        key = topology_key(offline)
        path = checkpoints / (key.replace(';', '_') + '.json')
        if path.exists():
            saved = json.loads(path.read_text())
            if saved.get('request_sha256') != request_sha256 or saved.get('status') != 'complete':
                raise ValueError('OPS checkpoint request identity mismatch')
            result, trace = (CandidateResult(**saved['result']), saved['continuous_rows'])
        else:
            result, trace = resident.evaluate_topology(offline, lambda_r)
            validate_candidate(result, trace, offline, search_id, output, payload_store=getattr(resident, 'payload_store', None), request_sha256=request_sha256)
            if result.evaluator != model_key or result.lambda_r != lambda_r:
                raise ValueError('resident returned the wrong evaluator/lambda')
            atomic_json(path, _plain(dict(status='complete', request_sha256=request_sha256, result=asdict(result), continuous_rows=trace)))
        validate_candidate(result, trace, offline, search_id, output, payload_store=getattr(resident, 'payload_store', None), request_sha256=request_sha256)
        if result.evaluator != model_key or result.lambda_r != lambda_r:
            raise ValueError('cached evaluator/lambda mismatch')
        continuous.extend((dict(evaluator=model_key, lambda_r=lambda_r, topology_key=key, **{k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v for k, v in item.items()}) for item in trace))
        return result
    rows.append(one(()))
    rows.extend((one(z) for z in k1))
    parents = sorted([r for r in rows if r.k == 1 and r.eligible], key=lambda r: (float(r.search_objective), r.topology_key))[:search_config['parent_count']]
    children = k2_children(parents=[(rank, _ids(r.offline_branch_ids)[0]) for rank, r in enumerate(parents, 1)], line_ids=identity.l_trans, weights=weights, c_by_line=costs, lambda_r=lambda_r, children_per_parent=search_config['k2_children_per_parent'], max_unique=search_config['k2_max_unique'])
    rows.extend((one(child.offline_branch_ids) for child in children))
    pd.DataFrame([_candidate_row(r) for r in rows]).to_parquet(output / f'{model_key}_candidate_results.parquet', index=False)
    pd.DataFrame([dict(evaluator=model_key, lambda_r=lambda_r, **c.as_dict()) for c in children]).to_parquet(output / f'{model_key}_k2_candidates.parquet', index=False)
    pd.DataFrame(continuous).to_parquet(output / f'{model_key}_continuous_evaluations.parquet', index=False)
    finalist = select_finalist(rows)
    pd.DataFrame([_candidate_row(finalist)]).to_parquet(output / f'{model_key}_finalists.parquet', index=False)
    summary = dict(status='PASS', evaluator=model_key, lambda_values=[lambda_r], attempted_states=len(rows), eligible_states=sum((r.eligible for r in rows)), finalist_count=1, request_sha256=request_sha256, search_id=search_id, actual_surrogate_calls=len(continuous), shared_k1_count=len(k1), k2_count=len(children), eligible_k1_parent_count=len(parents), k2_pruning_reasons=([f'Only {len(parents)} eligible K1 parents'] if len(parents) < search_config['parent_count'] else []) + (['K2 generation deduplicated or exhausted the prescribed child universe'] if len(children) < len(parents) * search_config['k2_children_per_parent'] else []), production_readiness_certified=False)
    atomic_json(output / f'{model_key}_run_summary.json', summary)
    return summary

def run_trajectory(**kwargs):
    from filelock import FileLock
    output = Path(kwargs['output']).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(output.parent / ('.' + output.name + '.trajectory.lock')), timeout=0):
        return _run_trajectory(**kwargs)
