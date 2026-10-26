"""Discover model/grid compatibility and local assets without importing ML packages."""

import json
from pathlib import Path

from .artifacts import checked_path, sha


STUDIES = ('goc_500', 'texas2k')
FINAL_TEXAS_REGIMES = ('G500', 'G100_to_R400', 'G100_to_W400')


def canonical_study(study):
    if study == 'goc500':
        study = 'goc_500'
    if study not in STUDIES:
        raise ValueError('study must be goc_500 or texas2k')
    return study


def model_spec(root, model_id, study=None):
    """Return the checksum-pinned catalog entry, rejecting cross-grid selection."""
    root = Path(root).resolve()
    catalog = json.loads((root / 'artifacts/model_catalog.json').read_text())
    if model_id not in catalog['models']:
        choices = ', '.join(sorted(catalog['models']))
        raise ValueError(f'unknown model ID {model_id!r}; choose from: {choices}')
    if not model_id.startswith(('goc500.', 'texas2k.')):
        raise ValueError('catalog model ID must declare its supported grid')
    inferred = 'goc_500' if model_id.startswith('goc500.') else 'texas2k'
    if study is not None and canonical_study(study) != inferred:
        raise ValueError(f'{model_id} belongs to {inferred}, not {study}')
    return dict(catalog['models'][model_id]), inferred


def asset_status(root, path, expected_sha256, *, verify_hashes=False):
    resolved = checked_path(root, path)
    present = resolved.is_file()
    digest = sha(resolved) if present and verify_hashes else None
    return dict(path=path, present=present, expected_sha256=expected_sha256,
                verified=digest == expected_sha256 if present and verify_hashes else None,
                sha256=digest)


def saved_case_path(root, spec, inputs=None):
    """Resolve the catalogued case, optionally from an authorized graph pack.

    A caller-supplied file/directory changes only where the bytes are read. The
    model catalog checksum remains mandatory before deserializing the case.
    """
    if inputs is None:
        return checked_path(root, spec['demo_input'])
    path = Path(inputs).resolve()
    if path.is_file():
        return path
    nested = path / spec['demo_input']
    if nested.is_file():
        return nested
    return path / Path(spec['demo_input']).name


def models(root, study=None, *, verify_hashes=False):
    """List every released/adapted checkpoint and its actual local readiness.

    Presence alone is labelled separately from checksum verification. A runnable
    saved-case input is not evidence that a historical population is distributed.
    """
    root = Path(root).resolve()
    if study is not None:
        study = canonical_study(study)
    catalog = json.loads((root / 'artifacts/model_catalog.json').read_text())
    rows = []
    for model_id in sorted(catalog['models']):
        spec, grid = model_spec(root, model_id)
        if study is not None and grid != study:
            continue
        assets = {name: asset_status(root, spec[name], spec[name + '_sha256']
                  if name != 'weights' else spec['sha256'], verify_hashes=verify_hashes)
                  for name in ('weights', 'normalizer', 'demo_input') if name in spec}
        available = lambda names: all(assets[name]['present'] and
                                     assets[name]['verified'] is not False for name in names)
        weight_names = [name for name in ('weights', 'normalizer') if name in assets]
        final = (grid == 'texas2k' and spec.get('scientific_certification') == 'PASS'
                 and model_id.rsplit('.', 1)[-1] in FINAL_TEXAS_REGIMES)
        role = ('base' if model_id.endswith('.base') else 'smoke' if model_id.endswith('.ft0')
                else 'intermediate' if model_id.endswith('.G100') else 'final')
        rows.append(dict(model_id=model_id, study=grid, family=spec['family'], role=role,
                         certification=spec.get('scientific_certification', spec.get('historical_role', 'UNSPECIFIED')),
                         ops_status=spec.get('ops', 'RECORDED_RESULTS_SEPARATE_FROM_SAMPLE_DEMO'),
                         selected_epoch=spec.get('selected_epoch'),
                         input_distribution=spec.get('input_distribution'), assets=assets,
                         weights_ready=available(weight_names),
                         saved_input_ready=available(['demo_input']),
                         saved_case_ready=available(assets),
                         supported_modes=['infer'] + (['demo'] if grid == 'goc_500' else [])
                                         + (['published'] if final else [])))
    return rows


def format_models(rows):
    """Human-readable CLI view; model IDs are also the Python/CLI selectors."""
    columns = [('MODEL ID', 'model_id'), ('FAMILY', 'family'), ('WEIGHTS', None),
               ('SAVED INPUT', None), ('MODES', None)]
    values = [[row['model_id'], row['family'], 'ready' if row['weights_ready'] else 'missing',
               'ready' if row['saved_input_ready'] else 'missing', ','.join(row['supported_modes'])]
              for row in rows]
    widths = [max([len(title), *(len(row[i]) for row in values)])
              for i, (title, _) in enumerate(columns)]
    lines = ['  '.join(title.ljust(width) for (title, _), width in zip(columns, widths))]
    lines.extend('  '.join(value.ljust(width) for value, width in zip(row, widths)) for row in values)
    lines.append('Ready = local files present; use --verify-hashes for checksum validation.')
    lines.append('Saved input = one catalogued case; published-population availability is separate.')
    return '\n'.join(lines)
