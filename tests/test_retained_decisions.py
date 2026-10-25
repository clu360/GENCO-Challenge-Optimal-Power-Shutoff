from pathlib import Path
import pandas as pd
import pytest
from genco_ops.results import recompute_retained_decision

ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('regime',['G500','G100_to_R400','G100_to_W400'])
def test_retained_physical_risk_service_and_line_ids(regime):
    table=pd.read_csv(ROOT/'experiments/texas2k/results/stage_m/tables/finalist_native_and_exact.csv')
    result=recompute_retained_decision(ROOT,regime)
    row=table.loc[table.model.eq(result['model'])].iloc[0]
    for name in ('native_r','a_r','shed','native_j','a_j'):
        assert result[name]==pytest.approx(row[name],rel=1e-10,abs=1e-10)
    assert result['offline_branch_ids']==list(map(int,row['topology_key'].split(';')))
    assert result['fresh_ops'] is False
