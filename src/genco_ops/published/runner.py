"""Explicit full Phase I OPS or bounded portability probe, using exported workers."""
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path

from ..artifacts import sha,verify
from .identity import load_identity
from .io import atomic_json
from .canonical import canonical
from .search import ALPHA_SEARCH_ID


SEARCH=dict(k1_count=50,parent_count=5,k2_children_per_parent=50,k2_max_unique=250,continuous_budget=20)


def plan(root,model_id,inputs,output,*,device,probe_topology=None):
    root=Path(root).resolve();inputs=Path(inputs).resolve();output=Path(output).resolve()
    config_path=root/'experiments/texas2k/configs/phase_i_original.json'
    config=json.loads(config_path.read_text())
    if (config['scenario']!=16 or config['lambda_r']!=.8 or config['controls']!='alpha_only'
            or config['topology']!=dict(K0=1,K1=50,K2_max=250,K1_parents=5)
            or config['continuous_objective_calls_per_topology_max']!=20):
        raise ValueError('frozen Phase I numerical settings changed')
    identity,contract=load_identity(inputs,config)
    if probe_topology is not None:
        if len(probe_topology)>2 or len(set(probe_topology))!=len(probe_topology) or any(
                type(line)!=int or line not in identity.l_trans for line in probe_topology):
            raise ValueError('a probe must use a valid K0/K1/K2 topology')
        if tuple(probe_topology)!=tuple(sorted(probe_topology)):
            raise ValueError('probe topology must be canonically sorted')
    elif device!='cuda:0':
        raise ValueError('the full search requires one CUDA GPU; no CPU substitution')
    if any(path==output or output in path.parents or path in output.parents for path in (inputs,root/'artifacts/cache')):
        raise ValueError('output must not overlap electrical inputs or immutable model cache')
    registry=json.loads((root/'artifacts/model_catalog.json').read_text())
    if model_id not in registry['models']:raise ValueError('checkpoint not yet certified/available')
    model=registry['models'][model_id]
    if (not model_id.startswith('texas2k.') or model.get('scientific_certification')!='PASS'
            or model_id.rsplit('.',1)[-1] not in config['selected_final_regimes']):
        raise ValueError('a certified final Phase I representative is required')
    request=dict(policy='PORTABLE_PUBLISHED_PHASE_I_OPS_V1',model_id=model_id,
        checkpoint_sha256=model['sha256'],family=model['family'],lambda_r=.8,
        r_base=config['risk_base'],search=SEARCH,search_id=ALPHA_SEARCH_ID,
        scope='BOUNDED_PORTABILITY_PROBE' if probe_topology is not None else 'FULL_PUBLISHED_CONFIGURATION',
        probe_topology=probe_topology,device=device,config_sha256=sha(config_path),
        input_contract_sha256=sha(inputs/'input_contract.json'),
        source_manifest_sha256=sha(Path(__file__).with_name('SOURCE_EXPORT.json')),
        public_model_catalog_sha256=sha(root/'artifacts/model_catalog.json'))
    if model['family']=='genco_opf':request['normalizer_sha256']=model['normalizer_sha256']
    request['identity_sha256']=hashlib.sha256(canonical(request).encode()).hexdigest()
    return request,identity


def run(root,model_id,inputs,output,*,device='cuda:0',execute=False,probe_topology=None):
    request,identity=plan(root,model_id,inputs,output,device=device,probe_topology=probe_topology)
    if not execute:return dict(status='VALIDATED_PLAN_NOT_EXECUTED',request=request,numerical_execution=False)
    verify(root)
    from filelock import FileLock
    output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    with FileLock(str(output.parent/('.'+output.name+'.portable.lock')),timeout=0):
        from .runtime import ResidentGENCO,ResidentGridSFM
        resident_type=ResidentGENCO if request['family']=='genco_opf' else ResidentGridSFM
        if probe_topology is not None:
            return _probe(request,resident_type,root,model_id,identity,output,device)
        from .trajectory import run_trajectory
        resident=resident_type(root,model_id,identity=identity,output=output,
            request_sha256=request['identity_sha256'],device=device,probe=False)
        return run_trajectory(resident=resident,identity=identity,prepared_dir=inputs,output=output,
            model_key=request['family'],lambda_r=.8,search_config=SEARCH,
            request_sha256=request['identity_sha256'],search_id=ALPHA_SEARCH_ID)


def _probe(request,resident_type,root,model_id,identity,output,device):
    from .schemas import CandidateResult
    from .trajectory import validate_candidate
    marker=output/'probe_identity.json'
    if marker.exists():
        if json.loads(marker.read_text())!=request:raise ValueError('probe identity changed')
    else:
        if output.exists() and any(output.iterdir()):raise ValueError('unowned probe directory; do not overwrite')
        output.mkdir(parents=True,exist_ok=True);atomic_json(marker,request)
    complete=output/'probe_result.json'
    if complete.exists():
        saved=json.loads(complete.read_text())
        if saved['request']!=request:raise ValueError('completed probe identity changed')
        result=CandidateResult(**saved['candidate'])
        validate_candidate(result,saved['trace'],tuple(request['probe_topology']),ALPHA_SEARCH_ID,output)
        return dict(status=saved['status'],reused_completed_output=True,new_model_calls=0,
            actual_surrogate_calls=len(saved['trace']),result=str(complete))
    resident=resident_type(root,model_id,identity=identity,output=output,
        request_sha256=request['identity_sha256'],device=device,probe=True)
    result,trace=resident.evaluate_topology(tuple(request['probe_topology']),.8)
    validate_candidate(result,trace,tuple(request['probe_topology']),ALPHA_SEARCH_ID,output)
    if not result.eligible:raise RuntimeError('probe has no finite eligible candidate; preserve failure evidence')
    record=dict(status='PASS_BOUNDED_ORIGINAL_CONTRACT_NOT_FULL_SEARCH',request=request,
        candidate=asdict(result),trace=trace,runtime=resident.runtime,
        full_historical_search_recomputed=False,new_ac_audit_executed=False)
    atomic_json(complete,record)
    return dict(status=record['status'],reused_completed_output=False,actual_surrogate_calls=len(trace),
        new_model_calls=result.metadata.get('new_model_calls',sum(not row.get('replayed_committed_call',False) for row in trace)),
        result=str(complete),r_norm=result.r_norm,l_shed=result.l_shed_total,j_trade=result.j_trade)
