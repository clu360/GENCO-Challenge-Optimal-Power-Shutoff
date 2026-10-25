"""Load every acquired catalog checkpoint through pinned official implementations."""
import argparse
import gc
import importlib.metadata as metadata
import json
from pathlib import Path
import platform

import torch
from genco_ops.artifacts import checked_path,sha,configure_native_cache
from genco_ops.model_loading import build_native_task

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
torch.set_num_threads(2)
catalog=json.loads((root/'artifacts/model_catalog.json').read_text())['models']
rows=[]
for model_id,spec in catalog.items():
    checkpoint=checked_path(root,spec['weights'])
    if sha(checkpoint)!=spec['sha256']:raise ValueError('checkpoint hash mismatch')
    if spec['family']=='genco_opf':
        normalizer=checked_path(root,spec['normalizer'])
        if sha(normalizer)!=spec['normalizer_sha256']:raise ValueError('normalizer mismatch')
        request=dict(spec['loader_request'],normalizer=str(normalizer))
        model,_=build_native_task(request,spec['loader_contract'],checkpoint)
    else:
        configure_native_cache(root)
        import gridsfm
        model=gridsfm.load_model(checkpoint,device='cpu')
    model.eval()
    row=dict(model_id=model_id,status='PASS_OFFICIAL_MODEL_LOAD',checkpoint_sha256=spec['sha256'],
        parameter_count=sum(p.numel() for p in model.parameters()),device='cpu',
        prediction_executed=False,physical_feasibility_certified=False)
    rows.append(row)
    print(json.dumps(row),flush=True)
    del model
    gc.collect()
result=dict(checks=rows,all_pass=True,python=platform.python_version(),platform=platform.system(),
    packages={name:metadata.version(name) for name in ('torch','torch_geometric','numpy','scipy',
        'huggingface_hub','gridfm-graphkit','gridsfm')},
    upstream={name:json.loads(metadata.distribution(name).read_text('direct_url.json'))['vcs_info']
        for name in ('gridfm-graphkit','gridsfm')})
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(result,indent=2))
