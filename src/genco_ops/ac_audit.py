"""Optional exact OPF A/B adapter consuming an explicit, fixed decision record.

The Julia numerical implementation is an unchanged export of the study source.
No solve is started by preparing/validating a command.
"""
import csv
import json
import math
from pathlib import Path
import subprocess
import time

from .artifacts import sha


def prepare(root,decision_path,case_path,output,*,julia='julia'):
    root=Path(root).resolve();output=Path(output).resolve()
    decision=json.loads(Path(decision_path).read_text())
    if decision.get('contract')!='OPF_FIXED_TOPOLOGY_SERVICE_A_AND_MAX_SERVICE_B_V1':
        raise ValueError('an explicit OPF reference decision contract is required')
    if sha(case_path)!=decision['case_sha256']:
        raise ValueError('the authorized electrical case differs from the decision')
    if not math.isfinite(decision['r_base']) or decision['r_base']<=0:
        raise ValueError('positive stored risk normalization required')
    if not 0<=decision['lambda_r']<=1:
        raise ValueError('lambda outside [0,1]')
    offline=decision['offline_branch_ids'];sourceless=decision['sourceless_load_ids']
    for values in (offline,sourceless):
        if len(values)!=len(set(values)) or any(type(v)!=int or v<0 for v in values):
            raise ValueError('canonical identities must be distinct zero-based integers')
    alpha=decision['alpha'];hazard=decision['p_env']
    if any(not math.isfinite(v) or not 0<=v<=1 for v in alpha.values()):
        raise ValueError('invalid fixed load service')
    if any(not math.isfinite(v) or v<0 for v in hazard.values()):
        raise ValueError('invalid exposure proxy')
    output.mkdir(parents=True,exist_ok=True)
    for name,header,values in [('alpha.csv',('load_id','alpha'),alpha),
                              ('p_env.csv',('powermodels_branch_id','p_env'),hazard)]:
        with (output/name).open('w',newline='') as handle:
            writer=csv.writer(handle);writer.writerow(header)
            for key,value in sorted(values.items(),key=lambda item:int(item[0])):
                writer.writerow([int(key)+1,value])
    project=root/'environments/julia';script=project/'stage_k_native_opf.jl'
    common=[julia,'--startup-file=no','--history-file=no','--project='+str(project),str(script),
        'reference_a',str(Path(case_path).resolve()),';'.join(str(i+1) for i in sorted(offline)),
        ';'.join(str(i+1) for i in sorted(sourceless)),str(output/'p_env.csv'),str(output/'alpha.csv'),
        str(decision['lambda_r']),str(decision['r_base']),str(output),
        str(decision['reference_b_service_tolerance_mw'])]
    b=common.copy();b[5]='reference_b';b[10]='-'
    plan=dict(status='PREPARED_NOT_EXECUTED',contract=decision['contract'],
        decision_sha256=sha(decision_path),case_sha256=sha(case_path),
        numerical_source_sha256=sha(script),commands=[common,b],
        input_hashes={str(Path(path).resolve()):sha(path)
            for path in (case_path,decision_path,script,output/'alpha.csv',output/'p_env.csv')},
        semantics=dict(A='economic AC-OPF at fixed topology and alpha',
            B1='maximum load delivery at fixed topology',B2='economic cost at B1 service'),
        full_numerical_reproduction_verified=False)
    (output/'audit_plan.json').write_text(json.dumps(plan,indent=2))
    return plan


def execute(plan,output,*,timeout_seconds=10800):
    """Run only after explicit user command; preserve exits and all solver evidence."""
    output=Path(output)
    for path,expected in plan['input_hashes'].items():
        if sha(path)!=expected:
            raise ValueError('audit input changed after preparation')
    if (output/'execution_intent.json').exists():
        raise RuntimeError('a prior AC execution exists; reconcile it, do not silently rerun')
    (output/'execution_intent.json').write_text(json.dumps(plan,indent=2))
    timings=[]
    for label,command in zip(('reference_a','reference_b'),plan['commands'],strict=True):
        start=time.perf_counter()
        with (output/(label+'_stdout.log')).open('w') as stdout, (output/(label+'_stderr.log')).open('w') as stderr:
            completed=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=timeout_seconds,check=False)
        timings.append(dict(mode=label,exit_code=completed.returncode,seconds=time.perf_counter()-start))
        (output/'process_results.json').write_text(json.dumps(timings,indent=2))
        if completed.returncode:raise RuntimeError('AC process failed; raw evidence retained')
    summaries={name:json.loads((output/(name+'_summary.json')).read_text())
        for name in ('reference_a','reference_b_b1','reference_b_b2')}
    eligible={'OPTIMAL','LOCALLY_SOLVED'}
    if any(summaries[name]['termination_status'] not in eligible for name in ('reference_a','reference_b_b1')):
        raise RuntimeError('A or B1 is not solver-eligible; no certified audit outcome')
    b2_ok=summaries['reference_b_b2']['termination_status'] in eligible
    result=dict(status='SOLVER_ELIGIBLE' if b2_ok else 'B1_ELIGIBLE_B2_REQUIRES_FAILURE_REVIEW',
        summaries=summaries,timings=timings,
        physical_quality_certified=False,
        reason='Run original numerical quality checks on exported physical tables; solver exit alone is insufficient')
    (output/'audit_execution.json').write_text(json.dumps(result,indent=2))
    return result
