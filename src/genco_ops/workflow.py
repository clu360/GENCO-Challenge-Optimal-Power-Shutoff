"""One model selector for the existing bounded and published numerical adapters.

Planning never imports torch, runs a solver, downloads assets, or changes data.
The adapters retain their original numerical budgets and provenance contracts.
"""

from pathlib import Path

from .artifacts import sha
from .catalog import asset_status, model_spec, models, saved_case_path


def validate_output(root, output):
    """Keep execution products separate from packaged source/evidence/assets."""
    root, output = Path(root).resolve(), Path(output).resolve()
    protected = ('src', 'artifacts', 'experiments', 'notebooks', 'docs',
                 'environments', 'scripts', 'tests', '.git', 'dist')
    if output == root or root.is_relative_to(output) or any(
            output.is_relative_to(root / name) for name in protected):
        raise ValueError('output must be separate from packaged source, evidence and models; use outputs/<run-name>')
    return output


def run_public_genco(root, output, *, scenario=0, execute=False):
    """Inspect or run the explicitly separate public IEEE14 GENCO example.

    This uses the released base checkpoint, rather than substituting IEEE14
    inputs for the Texas2k validation population in the model catalog.
    """
    from .public_genco_demo import run_public_demo, verify_public_data
    root = Path(root).resolve()
    output = validate_output(root, output)
    if type(scenario) is not int or scenario < 0:
        raise ValueError('scenario must be a nonnegative integer in the public fixture')
    manifest = verify_public_data(root)
    model_id = 'texas2k.genco_opf.base'
    row = next(item for item in models(root, 'texas2k') if item['model_id'] == model_id)
    missing = [row['assets'][name]['path'] for name in ('weights', 'normalizer')
               if not row['assets'][name]['present']]
    if execute:
        if missing:
            raise FileNotFoundError('Acquire the documented GENCO model bundle: ' + ', '.join(missing))
        return run_public_demo(root, output, model_id=model_id, scenario=scenario)
    return dict(status='MISSING_ARTIFACTS' if missing else 'PLAN_NOT_EXECUTED',
                demo_id='PUBLIC_IEEE14_GENCO_MASKED_OPF_V1', model_id=model_id,
                input_grid='PUBLIC_IEEE14', public_source_commit=manifest['source_commit'],
                scenario=scenario, output=str(output), missing_assets=missing,
                maximum_model_calls=1, numerical_execution=False, texas2k_result=False,
                fine_tuning_benefit_established=False, ac_feasibility_certified=False,
                scope='PUBLIC_SMALL_GRID_FUNCTIONAL_DEMO_OUT_OF_TRAINING_GRID')


def run_workflow(root, study, model_id, output, *, mode='infer', execute=False,
                 inputs=None, config=None, device=None, probe_topology=None):
    """Plan, or explicitly execute, a grid-compatible existing pipeline.

    ``infer`` predicts one hash-bound saved case. ``demo`` runs the distinct
    GOC official-sample OPS. ``published`` uses the frozen Texas Phase I runner;
    it requires an authorized prepared input directory and one CUDA GPU unless
    an explicit single-topology portability probe is requested.
    """
    root = Path(root).resolve()
    spec, study = model_spec(root, model_id, study)
    row = next(item for item in models(root, study)
               if item['model_id'] == model_id)
    output = validate_output(root, output)
    if mode not in row['supported_modes']:
        if mode == 'published' and study == 'goc_500':
            raise ValueError('the historical GOC full-search input population is not distributed; '
                             'use demo for fresh official-sample execution or results for recorded tables')
        raise ValueError(f'{model_id} supports modes: {", ".join(row["supported_modes"])}')
    if mode != 'published' and probe_topology is not None:
        raise ValueError('--probe-topology applies only to published Texas OPS')
    if mode == 'demo' and inputs is not None:
        raise ValueError('the bounded GOC demo uses its checksum-pinned official sample; --inputs applies to infer/published')
    if mode != 'demo' and config is not None:
        raise ValueError('--config applies only to the separate bounded GOC demo; published settings are frozen')
    default_device = 'cuda:0' if mode == 'published' and probe_topology is None else 'cpu'
    device = device or default_device
    if mode != 'published' and device != 'cpu':
        raise ValueError('saved-case inference and the bounded GOC demo use the documented CPU runtime')
    needed = ['weights'] + (['normalizer'] if 'normalizer' in row['assets'] else [])
    if mode in ('infer', 'demo'):
        needed.append('demo_input')
    if execute:
        for name in needed:
            item = row['assets'][name]
            row['assets'][name] = asset_status(root, item['path'], item['expected_sha256'], verify_hashes=True)
    if mode == 'infer' and inputs is not None:
        path = saved_case_path(root, spec, inputs)
        present = path.is_file()
        digest = sha(path) if execute and present else None
        row['assets']['demo_input'] = dict(path=str(path), present=present,
            expected_sha256=spec['demo_input_sha256'],
            verified=digest == spec['demo_input_sha256'] if execute and present else None)
    missing = [row['assets'][name]['path'] for name in needed if not row['assets'][name]['present']]
    mismatched = [row['assets'][name]['path'] for name in needed
                  if row['assets'][name]['verified'] is False]
    request = dict(study=study, model_id=model_id, family=spec['family'], mode=mode,
                   output=str(output), device=device, missing_assets=missing,
                   mismatched_assets=mismatched, checkpoint_sha256=spec['sha256'],
                   numerical_execution=False, ac_audit_executed=False,
                   checksum_verified=execute and not missing and not mismatched,
                   published_full_search_recomputed=False)
    if mode == 'demo':
        from .goc500_demo import load_demo_config
        config_path = Path(config) if config else root / 'experiments/goc_500/demo_config.json'
        demo_config = load_demo_config(config_path)
        request.update(config=str(config_path.resolve()), config_sha256=sha(config_path),
                       topology_count=2, maximum_model_calls=2 * demo_config['max_calls_per_topology'],
                       scope='OFFICIAL_SAMPLE_DEMO_NOT_PUBLISHED_GOC_POPULATION')
    elif mode == 'published':
        request.update(inputs=str(Path(inputs).resolve()) if inputs is not None else None,
                       scope='BOUNDED_PORTABILITY_PROBE' if probe_topology is not None
                             else 'FROZEN_TEXAS_PHASE_I_SEARCH',
                       maximum_topology_count=1 if probe_topology is not None else 301,
                       maximum_model_calls=20 if probe_topology is not None else 6020)
        if inputs is not None:
            from .published.runner import plan
            frozen, _ = plan(root, model_id, inputs, output, device=device, probe_topology=probe_topology)
            request['published_request'] = frozen
    else:
        request['scope'] = 'ONE_SAVED_CASE_NOT_AC_FEASIBILITY'
        request['input'] = row['assets']['demo_input']
    if mismatched:
        request['status'] = 'CHECKSUM_MISMATCH'
    elif missing:
        request['status'] = 'MISSING_ARTIFACTS'
    elif mode == 'published' and inputs is None:
        request['status'] = 'INPUTS_REQUIRED'
    else:
        request['status'] = 'READY_TO_EXECUTE' if execute else 'PLAN_NOT_EXECUTED'
    if not execute:
        return request
    if request['status'] != 'READY_TO_EXECUTE':
        raise ValueError(f'{request["status"]}: acquire the documented model/data assets; '
                         f'missing={missing}, mismatched={mismatched}; published mode also requires --inputs')
    if mode == 'infer':
        from .inference import predict_saved_case
        return predict_saved_case(root, model_id, output, inputs=inputs)
    if mode == 'demo':
        from .goc500_demo import run_demo
        return run_demo(root, model_id, output, config)
    from .published.runner import run
    return run(root, model_id, inputs, output, device=device, execute=True, probe_topology=probe_topology)
