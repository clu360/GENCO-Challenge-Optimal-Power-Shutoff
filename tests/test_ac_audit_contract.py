import json
from pathlib import Path
import pytest
from genco_ops.ac_audit import prepare
from genco_ops.artifacts import sha

ROOT=Path(__file__).resolve().parents[1]

def test_fixed_decision_command_and_ids(tmp_path):
    case=tmp_path/'case.m';case.write_text('fixture not executed')
    record=dict(contract='OPF_FIXED_TOPOLOGY_SERVICE_A_AND_MAX_SERVICE_B_V1',
        case_sha256=sha(case),offline_branch_ids=[117,281],sourceless_load_ids=[3],
        r_base=32.975425699285616,lambda_r=.8,alpha={'0':.9,'3':0.},
        p_env={'117':.2,'281':.1},reference_b_service_tolerance_mw=.0001)
    decision=tmp_path/'decision.json';decision.write_text(json.dumps(record))
    plan=prepare(ROOT,decision,case,tmp_path/'audit')
    a,b=plan['commands']
    assert a[5]=='reference_a' and b[5]=='reference_b'
    assert a[7]=='118;282' and a[8]=='4'
    assert b[10]=='-' and a[10].endswith('alpha.csv')
    assert '1,0.9' in (tmp_path/'audit/alpha.csv').read_text()
    assert plan['full_numerical_reproduction_verified'] is False
    record['case_sha256']='bad';decision.write_text(json.dumps(record))
    with pytest.raises(ValueError,match='differs'):prepare(ROOT,decision,case,tmp_path/'bad')
