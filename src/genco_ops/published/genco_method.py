from __future__ import annotations
import json,math,time
from pathlib import Path
import pandas as pd
from .journal import SurrogateJournal
from .search import sequential_powell
from .io import atomic_json
from ..artifacts import sha
from .support import _json_value
from .runtime import synchronize
class UnsupportedTopology(ValueError): pass
def evaluate_topology(self, offline, lambda_r):
    from .schemas import CandidateResult, ResultStatus
    from .service import select_topology_relative_loads
    from .topology import topology_key
    from .adapter import build_tables
    from .graphkit_physics import _prepare, _known_input_checks, _case_metrics
    from .redispatch import redispatch_from_r
    from .controls import _effective_controls
    selected = select_topology_relative_loads(self.identity, offline, q=self.selected_load_count)
    trace, fatal = ([], [])
    key = topology_key(offline)
    journal = SurrogateJournal(self.output / 'call_journals' / key.replace(';', '_'), dict(request_sha256=self.request_sha256, topology=list(offline), lambda_r=lambda_r, runtime=self.runtime), payload_store=getattr(self, 'payload_store', None))

    def compute(x):
        start = time.monotonic()
        row = dict(x=list(x), model_called=False)
        try:
            if fatal:
                raise ValueError('worker error already recorded; no further model calls')
            alpha = dict(zip(selected, x[:len(selected)], strict=True))
            r = dict(zip(self.redispatch_ids, x[len(selected):], strict=True))
            delta = redispatch_from_r(self.identity, r)
            tables = build_tables(self.identity, offline_branch_ids=offline, alpha_requested=alpha, redispatch_mw=delta)
            if len(tables.sourced_components) != 1:
                raise UnsupportedTopology('unsupported sourced-component count')
            effective, applied = _effective_controls(self.identity, tables, selected, self.redispatch_ids, delta)
            data, normalized, normalizer = _prepare(tables, self.contract['task'], self.stats, self.device)
            checks = _known_input_checks(tables, normalized, data, self.contract['task'], self.stats)
            if not all(checks.values()):
                raise ValueError('native known-input contract failed: ' + repr(checks))
            synchronize(self.device)
            inference_start = time.monotonic()
            with self.torch.inference_mode():
                row['model_called'] = True
                prediction = self.model(data.x_dict, data.edge_index_dict, data.edge_attr_dict, data.mask_dict)
            synchronize(self.device)
            inference_wall = time.monotonic() - inference_start
            metrics, decoded = _case_metrics(self.identity, tables, prediction, data, normalizer, lambda_r)
            value = float(metrics['j_trade_lambda_0p5'])
            eligible = bool(metrics['finite_output']) and math.isfinite(value)
            payload = dict(eligible=eligible, search_objective=value if eligible else None, status=ResultStatus.SUCCESS.value if eligible else ResultStatus.NUMERICAL_FAILURE.value, metrics=metrics, decoded=decoded, alpha_effective=tables.alpha_effective, r_by_generator=r, redispatch_mw=applied, effective_x=effective, inference_wall_seconds=inference_wall)
        except Exception as exc:
            if not isinstance(exc, UnsupportedTopology):
                fatal.append(exc)
            payload = dict(eligible=False, search_objective=None, status=ResultStatus.EVALUATOR_EXCEPTION.value, message=repr(exc), fatal_error=not isinstance(exc, UnsupportedTopology))
        payload['elapsed_seconds'] = time.monotonic() - start
        payload['model_called'] = row['model_called']
        if not payload['eligible']:
            payload.pop('decoded', None)
        return _json_value(payload)

    def evaluate(x):
        try:
            if fatal:
                payload, reused = (dict(eligible=False, search_objective=None, status=ResultStatus.EVALUATOR_EXCEPTION.value, model_called=False, message='worker stopped after invariant failure', elapsed_seconds=0.0), False)
            else:
                payload, reused = journal.call(x, lambda: compute(x))
                if payload.get('fatal_error') and (not fatal):
                    fatal.append(RuntimeError(payload['message']))
        except Exception as exc:
            fatal.append(exc)
            payload, reused = (dict(eligible=False, search_objective=None, elapsed_seconds=0.0, model_called=False, status=ResultStatus.EVALUATOR_EXCEPTION.value, message=repr(exc)), False)
        row = dict(x=list(x), replayed_committed_call=reused, **{k: v for k, v in payload.items() if k != 'decoded'})
        trace.append(row)
        return payload
    search = sequential_powell(alpha0=[1.0] * len(selected), alpha_bounds=[(0.0, 1.0)] * len(selected), r0=[0.0] * len(self.redispatch_ids), r_bounds=[(-1.0, 1.0)] * len(self.redispatch_ids), evaluate=evaluate)
    if fatal:
        (self.output / 'failures').mkdir(parents=True, exist_ok=True)
        atomic_json(self.output / 'failures' / (key.replace(';', '_') + '.json'), _json_value(dict(status='PAUSED_WORKER_ERROR', errors=list(map(repr, fatal)), trace=trace)))
        raise RuntimeError('unexpected OPS worker error; evidence preserved') from fatal[0]
    if len(trace) != len(search.trace) or len(trace) > 20:
        raise ValueError('actual OPS objective-call ledger mismatch')
    merged = [dict(row, **audit) for row, audit in zip(trace, search.trace, strict=True)]
    metadata = dict(search_id=search.search_id, search_blocks=list(search.blocks), continuous_trace=list(search.trace), checkpoint_sha256=self.request['checkpoint_sha256'], ops_control_policy='ORIGINAL_RAW_STAGE_L', experimental_ref_conditioning_enabled=False, normalizer_sha256=self.request['normalizer_sha256'], call_artifacts={p.relative_to(self.output).as_posix(): sha(p) for p in journal.root.glob('*.json')}, new_model_calls=sum((bool(r.get('model_called')) and (not r['replayed_committed_call']) for r in trace)), replayed_committed_calls=sum((r['replayed_committed_call'] for r in trace)))
    if journal.payload_store is not None:
        metadata['payload_database'] = str(journal.payload_store.path)
    common = dict(evaluator=self.request['family'], lambda_r=lambda_r, k=len(offline), topology_key=key, offline_branch_ids=';'.join(map(str, offline)), selected_load_ids=';'.join(map(str, selected)), metadata=metadata, elapsed_seconds=sum((row['elapsed_seconds'] for row in trace)))
    if search.best_payload is None:
        return (CandidateResult(**common, status=ResultStatus.EVALUATOR_EXCEPTION.value, message='no finite Stage M continuous candidate'), merged)
    best, state = (search.best_payload, self.output / 'state' / key.replace(';', '_'))
    state.mkdir(parents=True, exist_ok=True)
    decoded, metrics = (best['decoded'], best['metrics'])
    bus_ids = self.identity.buses.sort_values('canonical_bus_index').bus_id.astype(int).tolist()
    pd.DataFrame(dict(bus_id=bus_ids, **decoded['bus'])).to_parquet(state / 'bus_state.parquet', index=False)
    branch = decoded['branch']
    pd.DataFrame(dict(canonical_branch_id=branch['canonical_branch_id'], physical_loading=branch['loading'], forward_s_mva=branch['forward_s_mva'], reverse_s_mva=branch['reverse_s_mva'], p_from_mw=branch['p_from_mw'], q_from_mvar=branch['q_from_mvar'], p_to_mw=branch['p_to_mw'], q_to_mvar=branch['q_to_mvar'])).to_parquet(state / 'branch_state.parquet', index=False)
    ids = self.identity.generators.loc[self.identity.generators.GEN_STATUS > 0, 'canonical_generator_id'].astype(int)
    pd.DataFrame(dict(canonical_generator_id=ids, pg_mw=decoded['generator_pg_mw'])).to_parquet(state / 'generator_state.parquet', index=False)
    pd.DataFrame(dict(canonical_load_id=list(map(int, best['alpha_effective'])), alpha_effective=list(best['alpha_effective'].values()))).to_parquet(state / 'load_service.parquet', index=False)
    metadata.update(state_artifacts={p.relative_to(self.output).as_posix(): sha(p) for p in state.glob('*.parquet')}, best_r_by_generator=best['r_by_generator'], best_redispatch_mw=best['redispatch_mw'], redispatch_net_mw=sum(best['redispatch_mw'].values()), redispatch_half_l1_mw=0.5 * sum((abs(v) for v in best['redispatch_mw'].values())))
    return (CandidateResult(**common, status=best['status'], eligible=True, search_objective=best['search_objective'], j_trade=best['search_objective'], j_total=best['search_objective'], r_norm=metrics['r_norm'], l_shed_total=metrics['l_shed'], pac_operational=metrics['pac_operational'], pac_total=metrics['pac_operational'], max_loading=metrics['max_loading'], loading_gt_1_count=metrics['overloaded_lines'], alpha_effective_json=json.dumps(best['alpha_effective'], sort_keys=True), state_path=str(state)), merged)
