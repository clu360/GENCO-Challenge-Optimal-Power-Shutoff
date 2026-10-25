"""Compare the portable adapter against a retained, unchanged Stage L S1 fixture."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from genco_ops.artifacts import sha
from genco_ops.published.identity import load_identity
from genco_ops.published.adapter import build_tables
from genco_ops.published.graphkit_physics import _prepare,_known_input_checks,_args,_case_metrics

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--inputs',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
config=json.loads((root/'experiments/texas2k/configs/phase_i_original.json').read_text())
identity,_=load_identity(args.inputs,config)
fixture=args.inputs/'source_contract_fixture'
binding=json.loads((fixture/'fixture_manifest.json').read_text())
for name,expected in binding['files'].items():
    if sha(fixture/name)!=expected:raise ValueError('historical fixture changed')
summary=json.loads((fixture/'case_summary.json').read_text())
tables=build_tables(identity,offline_branch_ids=tuple(summary['offline_branch_ids']),
    alpha_requested={int(summary['alpha_changed_load_id']):.8})
catalog=json.loads((root/'artifacts/model_catalog.json').read_text())['models']['texas2k.genco_opf.base']
checkpoint=root/catalog['weights']
if sha(checkpoint)!=binding['base_checkpoint_sha256']:raise ValueError('historical base checkpoint differs')
stats=next(iter(torch.load(root/catalog['normalizer'],map_location='cpu',weights_only=True).values()))
expected_stats=json.loads((fixture/'normalization_metadata.json').read_text())['stats']
if {key:float(value) for key,value in stats.items()}!=expected_stats:raise ValueError('normalizer differs from fixture')
torch.set_num_threads(2)
data,normalized,normalizer=_prepare(tables,'OptimalPowerFlow',stats,torch.device('cpu'))
expected=torch.load(fixture/'normalized_model_input.pt',map_location='cpu',weights_only=True)
tensor_count=0
def compare(a,b):
    global tensor_count
    if isinstance(b,dict):
        if a.keys()!=b.keys():raise ValueError('normalized input schema differs')
        for key in b:compare(a[key],b[key])
    elif torch.is_tensor(b):
        if a.dtype!=b.dtype or a.shape!=b.shape or not torch.equal(a,b):
            raise ValueError('normalized input tensor differs from actual historical fixture')
        tensor_count+=1
    elif a!=b:raise ValueError('normalized input scalar differs')
compare(normalized.to_dict(),expected)
checks=_known_input_checks(tables,normalized,data,'OptimalPowerFlow',stats)
if not all(checks.values()):raise ValueError('known physical controls changed')
physical=json.loads((fixture/'physical_case_after_decisions.json').read_text())
table_diagnostics={}
for key,frame in [('bus',tables.bus),('gen',tables.gen),('branch',tables.branch)]:
    reference=pd.DataFrame(physical[key])
    if frame.columns.tolist()!=reference.columns.tolist() or frame.shape!=reference.shape:
        raise ValueError('physical adapter table schema changed')
    numeric=frame.select_dtypes(include='number').columns
    difference=np.abs(frame[numeric].to_numpy()-reference[numeric].to_numpy())
    table_diagnostics[key]=dict(rows=len(frame),maximum_absolute_numeric_difference=float(np.nanmax(difference)))
from gridfm_graphkit.models.gnn_heterogeneous_gns import GNS_heterogeneous
model=GNS_heterogeneous(_args('OptimalPowerFlow'))
weights=torch.load(checkpoint,map_location='cpu',weights_only=True)
model.load_state_dict({key.removeprefix('model.'):value for key,value in weights.items()},strict=True)
model.eval()
with torch.inference_mode():prediction=model(data.x_dict,data.edge_index_dict,data.edge_attr_dict,data.mask_dict)
recorded=torch.load(fixture/'raw_model_output.pt',map_location='cpu',weights_only=True)
prediction_difference={key:float((prediction[key].detach().cpu()-recorded[key]).abs().max()) for key in recorded}
metrics,_=_case_metrics(identity,tables,prediction,data,normalizer,.5)
result=dict(status='PASS_ORIGINAL_PREPROCESSING_TENSORS_AND_CONTROLS',
    normalized_tensor_count=tensor_count,normalized_tensors_bitwise_equal=True,
    actual_historical_fixture=True,new_label_generation=False,source_fixture_sha256=sha(fixture/'fixture_manifest.json'),
    known_input_checks=checks,physical_table_diagnostics=table_diagnostics,
    finite_prediction=bool(all(torch.isfinite(value).all() for value in prediction.values())),
    recorded_prediction_max_abs_differences=prediction_difference,
    cross_runtime_bitwise_prediction_parity_claimed=False,
    current_metrics=metrics,recorded_r_norm=summary['r_norm'],
    current_r_norm_difference=metrics['r_norm']-summary['r_norm'],
    fixture_lambda_r=.5,phase_i_search_lambda_r=.8,full_search_recomputed=False)
if not result['finite_prediction']:raise ValueError('nonfinite prediction')
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2))
print(json.dumps(result))
