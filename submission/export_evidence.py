"""Freeze compact publication tables from results already included in this repository.

No original development checkout, model execution, or AC solve is needed.
The figure/PDF builder itself uses only the exported data/ directory.
"""
from pathlib import Path
import hashlib
import json

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / 'data'
SOURCES = []


def read(relative):
    path = ROOT / relative
    SOURCES.append({'path': relative, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    return pd.read_parquet(path) if path.suffix == '.parquet' else pd.read_csv(path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    prefix = 'experiments/texas2k/results/stage_m/tables/'
    physical = read(prefix + 'physical_validation.csv')
    rows = []
    for model, token in [('G500', 'G500'), ('G→R', 'G100_to_R400'), ('G→W', 'G100_to_W400')]:
        for dist in ['G', 'R', 'W']:
            # Historical physical-validation tables use O for wildfire/outage distribution.
            observed = 'O' if dist == 'W' and 'W' not in set(physical.distribution) else dist
            d = physical[physical.checkpoint_task.str.contains('genco_opf.' + token + '.', regex=False)
                         & physical.distribution.eq(observed)]
            assert len(d) == 100, (model, dist, len(d))
            rows.append(dict(model=model, distribution=dist, cases=len(d),
                mean_bus_abs_p_mw=d.mean_abs_p_residual_mw.mean(),
                mean_bus_abs_q_mvar=d.mean_abs_q_residual_mvar.mean(),
                mean_worst_bus_abs_p_mw=d.max_abs_p_residual_mw.mean(),
                mean_worst_bus_abs_q_mvar=d.max_abs_q_residual_mvar.mean()))
    pd.DataFrame(rows).to_csv(OUT / 'texas_validation.csv', index=False)
    exact = read(prefix + 'finalist_native_and_exact.csv')
    assert len(exact) == 3
    exact.to_csv(OUT / 'texas_selected_ac.csv', index=False)
    refined = 'experiments/goc_500/results/refined_study/core_results/'
    state = read(refined + 'state_fidelity_all.parquet')
    refs = read(refined + 'reference_a_all.parquet')
    methods = ['Guided-GridSFM (released v1.1)', 'Guided-GridSFM (FullTop-1000)',
               'Guided-GridSFM (FullTop-1500)', 'Guided-GridSFM (FullTop+N-1)']
    rows = []
    for label, method in zip(['M0', 'M1', 'M2', 'M3'], methods):
        s = state[state.method.eq(method)]
        d = refs[refs.method.eq(method)]
        assert len(d) == 15
        rows.append(dict(model=label, mean_state_nrmse=s.nrmse.mean(),
            mean_abs_risk_discrepancy=(d.native_r_norm-d.reference_a_r_norm_ac).abs().mean(),
            mean_abs_objective_discrepancy=(d.native_j_trade-d.reference_a_j_true).abs().mean(),
            native_mean_j=d.native_j_trade.mean(), audited_mean_j=d.reference_a_j_true.mean(),
            selected_decisions=len(d)))
    pd.DataFrame(rows).to_csv(OUT / 'goc_agreement.csv', index=False)
    source = ROOT / 'experiments/goc_500/results/rq1/rq1_runtime_summary.json'
    SOURCES.append({'path': source.relative_to(ROOT).as_posix(),
                    'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
    (OUT / 'goc_runtime.json').write_bytes(source.read_bytes())
    facts = {'schema': 'COMPACT_PUBLICATION_EVIDENCE_V2',
        'evidence_cut': '2026-10-25; eight Texas fits certified, native GridSFM OPS pending',
        'source_files': SOURCES,
        'selection': 'GENCO-OPF final fits, 100 validation cases per G/R/W distribution; three selected Texas decisions; 15 common settings per GOC checkpoint, each model selecting its own decision; separate 54-decision M0 runtime benchmark',
        'scope': 'Aggregation of retained results, not fresh inference or AC recomputation',
        'exports': {p.name: {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
                    for p in sorted(OUT.iterdir()) if p.is_file() and p.suffix in {'.csv', '.json'} and p.name != 'provenance.json'}}
    (OUT / 'provenance.json').write_text(json.dumps(facts, indent=2), encoding='utf-8')
    print('Exported 9 validation summaries, 3 Texas selections, 4 GOC checkpoint summaries and runtime evidence.')


if __name__ == '__main__':
    main()
