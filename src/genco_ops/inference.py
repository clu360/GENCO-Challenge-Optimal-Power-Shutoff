"""Official checkpoint inference on explicitly acquired, checksum-verified cases."""

import json
from pathlib import Path
import time

from .artifacts import checked_path,sha,configure_native_cache


def predict_saved_case(root,model_id,output,inputs=None):
    from .catalog import model_spec, saved_case_path
    from .workflow import validate_output
    root=Path(root).resolve()
    output=validate_output(root,output)
    if any((output/name).exists() for name in ('prediction.pt','inference.json')):
        raise ValueError('preserve the existing prediction; choose a fresh output directory')
    spec,_=model_spec(root,model_id)
    checkpoint=checked_path(root,spec['weights'])
    if not checkpoint.exists():raise FileNotFoundError('Acquire the documented model bundle first')
    if sha(checkpoint)!=spec['sha256']:raise ValueError('checkpoint differs from catalog')
    fixture=saved_case_path(root,spec,inputs)
    if not fixture.exists():raise FileNotFoundError('This input is not distributed publicly; see the documented input-permission limitation')
    if sha(fixture)!=spec['demo_input_sha256']:raise ValueError('demo input differs')
    import torch
    torch.set_num_threads(2);torch.manual_seed(0);torch.use_deterministic_algorithms(True)
    started=time.perf_counter()
    if spec['family']=='genco_opf':
        from .model_loading import build_native_task
        request=dict(spec['loader_request'])
        normalizer=checked_path(root,spec['normalizer'])
        if sha(normalizer)!=spec['normalizer_sha256']:raise ValueError('normalizer differs')
        request['normalizer']=str(normalizer)
        task,_=build_native_task(request,spec['loader_contract'],checkpoint);task.eval()
        graph=torch.load(fixture,weights_only=False,map_location='cpu')
        with torch.inference_mode():predictions=task.model(graph.x_dict,graph.edge_index_dict,graph.edge_attr_dict,graph.mask_dict)
        predictions={k:v.detach().cpu() for k,v in predictions.items()}
        schema='GraphKit bus [Vm,Va,Pg,Qg], generator [Pg]; released power normalization'
    else:
        configure_native_cache(root)
        import gridsfm
        model=gridsfm.load_model(checkpoint,device='cpu');model.eval()
        if fixture.name.endswith('.pyg.json'):
            result=gridsfm.predict(model,fixture)
            predictions={k:v for k,v in result.items() if isinstance(v,torch.Tensor)}
        else:
            graph=torch.load(fixture,weights_only=False,map_location='cpu')
            batch=gridsfm.batch_data_list([graph])
            with torch.inference_mode():model(batch)
            predictions={k:batch[k].pred.detach().cpu() for k in ('bus','generator')}
        schema='Native v1.1 schema; bus [Va,Vm], generator [Pg,Qg]; native power normalization'
    if not predictions or any(not torch.isfinite(t).all() for t in predictions.values()):
        raise ValueError('nonfinite prediction')
    output.mkdir(parents=True,exist_ok=True)
    torch.save(predictions,output/'prediction.pt')
    result=dict(status='PASS_FINITE_INFERENCE_NOT_AC_FEASIBILITY',model_id=model_id,
        checkpoint_sha256=sha(checkpoint),demo_input_sha256=sha(fixture),schema=schema,
        input_path=str(fixture),
        device='cpu',torch=torch.__version__,seconds=time.perf_counter()-started,
        shapes={k:list(v.shape) for k,v in predictions.items()},
        published_production_result=False,ops_executed=False,ac_audit_executed=False)
    (output/'inference.json').write_text(json.dumps(result,indent=2))
    return result
