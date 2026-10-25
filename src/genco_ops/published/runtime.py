"""Explicit runtime transport for the exported resident evaluators."""
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import sys

from ..artifacts import checked_path,sha,configure_native_cache


COMMITS={'gridfm-graphkit':'95b90eecc7f5c2c86a9dd776f0c3f40434def22f',
         'gridsfm':'1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6'}


def synchronize(device):
    if device.type=='cuda':
        import torch
        torch.cuda.synchronize(device)


def load_runtime(root,model_id,device,*,probe):
    # These are the existing worker's environment values, not new numerical tuning.
    os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
    os.environ['HF_HUB_OFFLINE']='1'
    configure_native_cache(root)
    import torch
    for package,expected in COMMITS.items():
        actual=json.loads(metadata.distribution(package).read_text('direct_url.json'))
        if actual.get('vcs_info',{}).get('commit_id')!=expected:
            raise ValueError('install the pinned official '+package+' source')
    target=torch.device(device)
    if target.type=='cpu' and not probe:
        raise ValueError('full published OPS requires an explicit allocated CUDA device; CPU is probe-only')
    if target.type=='cuda' and (not torch.cuda.is_available() or torch.cuda.device_count()!=1 or str(target)!='cuda:0'):
        raise ValueError('one visible CUDA GPU at cuda:0 is required; no silent CPU fallback')
    root=Path(root).resolve()
    catalog=json.loads((root/'artifacts/model_catalog.json').read_text())
    if model_id not in catalog['models']:raise ValueError('checkpoint is not available/certified in this export')
    spec=catalog['models'][model_id]
    if (not model_id.startswith('texas2k.') or spec.get('scientific_certification')!='PASS'
            or model_id.rsplit('.',1)[-1] not in ('G500','G100_to_R400','G100_to_W400')):
        raise ValueError('choose a certified final Phase I representative, not G100 or a historical base')
    checkpoint=checked_path(root,spec['weights'])
    if sha(checkpoint)!=spec['sha256']:raise ValueError('selected checkpoint changed')
    torch.set_num_threads(2)
    return spec,checkpoint,torch,target


def fingerprint(torch,device):
    import numpy as np
    import scipy
    from . import search,journal
    return dict(torch=torch.__version__,cuda=torch.version.cuda,python=sys.version,
        device=torch.cuda.get_device_name(0) if device.type=='cuda' else 'cpu',numpy=np.__version__,scipy=scipy.__version__,
        deterministic=torch.are_deterministic_algorithms_enabled(),tf32=torch.backends.cuda.matmul.allow_tf32,
        cublas_workspace=os.environ.get('CUBLAS_WORKSPACE_CONFIG'),
        search_sha256=sha(search.__file__),journal_sha256=sha(journal.__file__),
        resident_sha256=sha(__file__))


class ResidentGENCO:
    def __init__(self,root,model_id,*,identity,output,request_sha256,device,probe):
        from .graphkit_physics import _args
        from gridfm_graphkit.models.gnn_heterogeneous_gns import GNS_heterogeneous
        spec,checkpoint,torch,target=load_runtime(root,model_id,device,probe=probe)
        self.torch,self.device=torch,target
        self.identity,self.output,self.request_sha256=identity,Path(output).resolve(),request_sha256
        self.selected_load_count=5
        self.contract=spec['loader_contract']
        self.request=dict(family='genco_opf',checkpoint_sha256=spec['sha256'],normalizer_sha256=spec['normalizer_sha256'])
        normalizer=checked_path(root,spec['normalizer'])
        if sha(normalizer)!=spec['normalizer_sha256']:raise ValueError('released normalization changed')
        self.model=GNS_heterogeneous(_args(self.contract['task']))
        weights=torch.load(checkpoint,map_location='cpu',weights_only=True)
        self.model.load_state_dict({key.removeprefix('model.'):value for key,value in weights.items()},strict=True)
        self.model.to(target).eval()
        stats=torch.load(normalizer,map_location='cpu',weights_only=True)
        if len(stats)!=1:raise ValueError('one frozen normalizer required')
        self.stats=next(iter(stats.values()))
        self.redispatch_ids=()
        self.runtime=fingerprint(torch,target)

    def evaluate_topology(self,offline,lambda_r):
        from .genco_method import evaluate_topology
        return evaluate_topology(self,offline,lambda_r)


class ResidentGridSFM:
    def __init__(self,root,model_id,*,identity,output,request_sha256,device,probe):
        from .native_raw import build_raw_gridsfm_case
        from ..demo_physics import build_goc500_identity
        spec,checkpoint,torch,target=load_runtime(root,model_id,device,probe=probe)
        import gridsfm
        self.identity,self.output,self.request_sha256=identity,Path(output).resolve(),request_sha256
        self.request=dict(family='opengridsfm',checkpoint_sha256=spec['sha256'],r_base=32.975425699285616)
        self.raw=build_raw_gridsfm_case(identity)
        self.raw_identity=build_goc500_identity(self.raw,candidate_branch_ids=identity.l_trans)
        self.model=gridsfm.load_model(checkpoint,device=str(target));self.model.eval()
        self.runtime=fingerprint(torch,target)
        rows=identity.branches.set_index('canonical_branch_id')
        self.p_env={line:float(rows.loc[line,'p_env']) for line in identity.l_trans}

    def evaluate_topology(self,offline,lambda_r):
        from .native_method import evaluate_topology
        return evaluate_topology(self,offline,lambda_r)
