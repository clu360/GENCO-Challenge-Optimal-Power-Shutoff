from __future__ import annotations
from dataclasses import asdict
import json,math,time
from pathlib import Path
import pandas as pd
from .journal import SurrogateJournal
from .search import sequential_powell
from .io import atomic_json
from ..artifacts import sha
from .support import _json_value
def evaluate_topology(self, offline, lambda_r):
    from .native_evaluator import evaluate_gridsfm_candidate
    from .native_schemas import PacWeights
    from .identity import source_less_load_ids
    from .service import select_topology_relative_loads
    from .schemas import CandidateResult, ResultStatus
    from .topology import topology_key
    key = topology_key(offline)
    selected = select_topology_relative_loads(self.identity, offline, q=5, exclude_load_ids=source_less_load_ids(self.identity, offline))
    journal = SurrogateJournal(self.output / 'call_journals' / key.replace(';', '_'), dict(request_sha256=self.request_sha256, topology=list(offline), lambda_r=lambda_r, runtime=self.runtime), payload_store=getattr(self, 'payload_store', None))
    trace, fatal = ([], [])

    def compute(x):
        started = time.monotonic()
        alpha = {int(line): 1.0 for line in self.identity.loads.canonical_load_id}
        alpha.update(dict(zip(selected, x, strict=True)))
        result = evaluate_gridsfm_candidate(raw_case=self.raw, identity=self.raw_identity, model=self.model, offline_branch_ids=offline, alpha_requested=alpha, p_env_by_line=self.p_env, r_base=self.request['r_base'], lambda_r=lambda_r, weights=PacWeights(rho_phys=2.0, w_op=1.0, w_ac=1.0, w_model=0.0))
        if result.objective is None or not math.isfinite(result.objective.j_total):
            return dict(eligible=False, search_objective=None, fatal_error=True, message=result.message, status=ResultStatus.EVALUATOR_EXCEPTION.value, elapsed_seconds=time.monotonic() - started)
        names = ('flow_loading_by_line', 'p_from_by_line', 'q_from_by_line', 'p_to_by_line', 'q_to_by_line', 'pg_by_generator', 'qg_by_generator', 'v_by_bus', 'theta_by_bus')
        state = {name: dict(getattr(result, name)) for name in names}
        if any((not values or any((not math.isfinite(float(value)) for value in values.values())) for values in state.values())):
            return dict(eligible=False, search_objective=None, fatal_error=True, message='native prediction contains incomplete or nonfinite electrical state', status=ResultStatus.NUMERICAL_FAILURE.value, elapsed_seconds=time.monotonic() - started)
        effective = result.load_shedding.alpha_effective
        return _json_value(dict(eligible=True, search_objective=result.objective.j_total, status=ResultStatus.SUCCESS.value, objective=asdict(result.objective), state=state, alpha_effective=dict(effective), effective_x=[effective[line] for line in selected], elapsed_seconds=time.monotonic() - started))

    def evaluate(x):
        try:
            if fatal:
                return dict(eligible=False, search_objective=None, status='WORKER_STOPPED')
            payload, replayed = journal.call(x, lambda: compute(x))
            trace.append(dict(replayed_committed_call=replayed, **{name: value for name, value in payload.items() if name not in ('state', 'alpha_effective')}))
            if payload.get('fatal_error'):
                fatal.append(payload.get('message'))
            return payload
        except Exception as exc:
            fatal.append(repr(exc))
            raise
    search = sequential_powell(alpha0=[1.0] * len(selected), alpha_bounds=[(0.0, 1.0)] * len(selected), evaluate=evaluate)
    if fatal:
        path = self.output / 'failures' / (key.replace(';', '_') + '.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(path, dict(status='PAUSED_WORKER_ERROR', errors=fatal))
        raise RuntimeError('native OPS invariant failure; preserve committed calls')
    if len(trace) != len(search.trace) or len(trace) > 20 or search.best_payload is None:
        raise ValueError('native OPS call accounting or eligible-incumbent failure')
    best = search.best_payload
    state = {name: {int(index): value for index, value in values.items()} for name, values in best['state'].items()}
    directory = self.output / 'state' / key.replace(';', '_')
    directory.mkdir(parents=True, exist_ok=True)
    branch_ids = sorted(state['flow_loading_by_line'])
    pd.DataFrame(dict(canonical_branch_id=branch_ids, physical_loading=[state['flow_loading_by_line'][i] for i in branch_ids], **{column: [100.0 * state[field][i] for i in branch_ids] for column, field in (('p_from_mw', 'p_from_by_line'), ('q_from_mvar', 'q_from_by_line'), ('p_to_mw', 'p_to_by_line'), ('q_to_mvar', 'q_to_by_line'))})).to_parquet(directory / 'branch_state.parquet', index=False)
    bus_ids = sorted(state['v_by_bus'])
    pd.DataFrame(dict(bus_id=bus_ids, vm=[state['v_by_bus'][i] for i in bus_ids], va=[state['theta_by_bus'][i] for i in bus_ids])).to_parquet(directory / 'bus_state.parquet', index=False)
    gen_ids = self.identity.generators.loc[self.identity.generators.GEN_STATUS > 0, 'canonical_generator_id'].astype(int).tolist()
    pd.DataFrame(dict(canonical_generator_id=gen_ids, pg_mw=[100.0 * state['pg_by_generator'][i] for i in range(len(gen_ids))])).to_parquet(directory / 'generator_state.parquet', index=False)
    alpha = dict(sorted(((int(i), value) for i, value in best['alpha_effective'].items())))
    pd.DataFrame(dict(canonical_load_id=list(alpha), alpha_effective=list(alpha.values()))).to_parquet(directory / 'load_service.parquet', index=False)
    objective = best['objective']
    metadata = dict(search_id=search.search_id, search_blocks=list(search.blocks), checkpoint_sha256=self.request['checkpoint_sha256'], ops_control_policy='ORIGINAL_RAW_STAGE_L', experimental_ref_conditioning_enabled=False, state_artifacts={p.relative_to(self.output).as_posix(): sha(p) for p in directory.glob('*.parquet')}, call_artifacts={p.relative_to(self.output).as_posix(): sha(p) for p in journal.root.glob('*.json')})
    if journal.payload_store is not None:
        metadata['payload_database'] = str(journal.payload_store.path)
    result = CandidateResult(evaluator='opengridsfm', lambda_r=lambda_r, k=len(offline), topology_key=key, offline_branch_ids=';'.join(map(str, offline)), status=ResultStatus.SUCCESS.value, eligible=True, search_objective=best['search_objective'], selected_load_ids=';'.join(map(str, selected)), alpha_effective_json=json.dumps(alpha, sort_keys=True), state_path=str(directory), metadata=metadata, elapsed_seconds=sum((row['elapsed_seconds'] for row in trace)), max_loading=max(state['flow_loading_by_line'].values()), loading_gt_1_count=sum((value > 1.0 for value in state['flow_loading_by_line'].values())), **{name: objective[name] for name in ('r_norm', 'l_shed_total', 'j_trade', 'pac_operational', 'pac_ac', 'pac_model', 'pac_total', 'j_total')})
    return (result, [dict(row, **audit) for row, audit in zip(trace, search.trace, strict=True)])
