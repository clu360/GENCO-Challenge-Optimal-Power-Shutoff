"""Real GENCO inference on the pinned public GraphKit IEEE14 fixture.

This is a public small-case compatibility example. It supplies no Texas2k
accuracy, fine-tuning benefit, wildfire-OPS, or AC-feasibility claim.
"""
import json
from pathlib import Path
import shutil
import time

from .artifacts import checked_path, sha
from .catalog import model_spec


def verify_public_data(root):
    root = Path(root).resolve()
    path = root / 'experiments/ieee14_public/data_manifest.json'
    manifest = json.loads(path.read_text())
    if manifest.get('schema') != 'PUBLIC_GRAPHKIT_CASE14_FIXTURE_V1':
        raise ValueError('unsupported public IEEE14 fixture manifest')
    if not manifest.get('public_git_tree_blob_parity'):
        raise ValueError('public upstream fixture provenance is required')
    raw = root / 'experiments/ieee14_public/data'
    actual = {path.relative_to(root).as_posix() for path in raw.rglob('*') if path.is_file()}
    if actual != set(manifest['files']):
        raise ValueError('public IEEE14 fixture file inventory differs from the pinned manifest')
    for relative, item in manifest['files'].items():
        source = checked_path(root, relative)
        if not source.is_file() or sha(source) != item['sha256']:
            raise ValueError('public IEEE14 fixture checksum differs: ' + relative)
    return manifest


def run_public_demo(root, output, *, model_id='texas2k.genco_opf.base', scenario=0):
    """Run one real masked OPF prediction with frozen released normalization.

    Raw fixture processing uses the pinned official GraphKit dataset class. All
    generated graphs are written under the caller's new output directory.
    """
    from .workflow import validate_output
    from .model_loading import build_native_task
    import torch
    import pandas as pd
    from gridfm_graphkit.datasets.powergrid_hetero_dataset import HeteroGridDatasetDisk
    from gridfm_graphkit.datasets.task_transforms import OptimalPowerFlowTransforms

    root = Path(root).resolve()
    output = validate_output(root, output)
    if output.exists() and any(output.iterdir()):
        raise ValueError('preserve the existing public demo; choose a fresh output directory')
    if type(scenario) is not int or scenario < 0:
        raise ValueError('scenario must be a nonnegative integer in the public fixture')
    manifest = verify_public_data(root)
    if model_id != 'texas2k.genco_opf.base':
        raise ValueError('the public IEEE14 functionality demo uses only the released GENCO-OPF base checkpoint')
    spec, _ = model_spec(root, model_id)
    for name, digest in [('weights', spec['sha256']), ('normalizer', spec['normalizer_sha256'])]:
        path = checked_path(root, spec[name])
        if not path.is_file():
            raise FileNotFoundError('Acquire the documented GENCO model bundle before running this public demo')
        if sha(path) != digest:
            raise ValueError('model/normalizer checksum differs: ' + name)
    torch.set_num_threads(2)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    started = time.perf_counter()
    request = dict(spec['loader_request'])
    request['normalizer'] = str(checked_path(root, spec['normalizer']))
    task, _ = build_native_task(request, spec['loader_contract'], checked_path(root, spec['weights']))
    task.eval()
    output.mkdir(parents=True, exist_ok=True)
    source_root = root / 'experiments/ieee14_public/data'
    raw = output / 'dataset/raw'
    shutil.copytree(source_root, raw)
    dataset = HeteroGridDatasetDisk(str(output / 'dataset'), task.data_normalizers[0],
                                  transform=OptimalPowerFlowTransforms(task.args))
    if scenario >= len(dataset):
        raise ValueError(f'scenario is outside the public fixture (0 through {len(dataset)-1})')
    graph = dataset[scenario]
    with torch.inference_mode():
        predictions = task.model(graph.x_dict, graph.edge_index_dict, graph.edge_attr_dict, graph.mask_dict)
    predictions = {key: value.detach().cpu() for key, value in predictions.items()}
    if not predictions or any(not torch.isfinite(value).all() for value in predictions.values()):
        raise ValueError('public GENCO inference produced nonfinite values')
    torch.save(predictions, output / 'prediction_normalized.pt')
    decoded = {key: value.clone() for key, value in predictions.items()}
    task.data_normalizers[0].inverse_output(decoded, None)
    bus = pd.DataFrame(decoded['bus'].numpy(), columns=['vm_pu', 'va_rad', 'pg_mw', 'qg_mvar'])
    bus.index.name = 'fixture_bus_index'
    bus.to_csv(output / 'predicted_bus.csv')
    generator = pd.DataFrame(decoded['gen'].numpy(), columns=['pg_mw'])
    generator.index.name = 'fixture_generator_index'
    generator.to_csv(output / 'predicted_generator.csv')
    result = dict(
        status='PASS_PUBLIC_GENCO_INFERENCE_NOT_AC_FEASIBILITY',
        demo_id='PUBLIC_IEEE14_GENCO_MASKED_OPF_V1', model_id=model_id,
        checkpoint_sha256=spec['sha256'], normalizer_sha256=spec['normalizer_sha256'],
        public_data_manifest_sha256=sha(root / 'experiments/ieee14_public/data_manifest.json'),
        public_source_commit=manifest['source_commit'], scenario=scenario,
        available_saved_scenarios=len(dataset), bus_count=len(bus), generator_count=len(generator),
        input_contract='ORIGINAL_GRAPHKIT_NORMALIZER_AND_OPTIMAL_POWER_FLOW_MASKS',
        output_schema='bus [Vm_pu,Va_rad,Pg_MW,Qg_MVAr]; generator [Pg_MW]',
        device='cpu', torch=torch.__version__, actual_model_calls=1,
        elapsed_seconds=time.perf_counter() - started,
        texas2k_result=False, historical_population_reproduced=False,
        fine_tuning_benefit_established=False, ac_feasibility_certified=False,
        training_executed=False, ops_search_executed=False, ac_audit_executed=False,
        scope='PUBLIC_SMALL_GRID_COMPATIBILITY_DEMO_SEPARATE_FROM_TEXAS_STUDY',
    )
    (output / 'public_demo.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result
