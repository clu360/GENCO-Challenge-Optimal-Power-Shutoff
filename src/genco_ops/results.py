"""Inspect retained results without model, GPU, network, or solver dependencies.

Every figure comes from packaged observations. These functions do not execute
inference, topology search, training, or AC optimization.
"""

import json
from pathlib import Path

GOC_METHODS = {
    'DC': 'Guided-DC',
    'M0': 'Guided-GridSFM (released v1.1)',
    'M1': 'Guided-GridSFM (FullTop-1000)',
    'M2': 'Guided-GridSFM (FullTop-1500)',
    'M3': 'Guided-GridSFM (FullTop+N-1)',
}


def recompute_retained_decision(root, regime):
    """Recompute a stored finalist from retained load/branch state diagnostics."""
    from .objectives import compute_r_norm, compute_l_shed, compute_j_trade
    if regime not in ('G500', 'G100_to_R400', 'G100_to_W400'):
        raise ValueError('unknown completed GENCO regime')
    path = Path(root) / 'experiments/texas2k/results/stage_m/retained_decisions' / (regime + '.json')
    record = json.loads(path.read_text())
    mappings = {name: {int(k): float(v) for k, v in record[name].items()}
                for name in ('alpha', 'p_env', 'pd_normalized_weights', 'native_loading', 'exact_a_loading')}
    shed = compute_l_shed(mappings['pd_normalized_weights'], mappings['alpha'])
    risk = {state: compute_r_norm(mappings['p_env'], record['offline_branch_ids'], mappings['p_env'],
                                 mappings[state + '_loading'], record['r_base'])
            for state in ('native', 'exact_a')}
    return dict(model=record['model'], offline_branch_ids=record['offline_branch_ids'],
                native_r=risk['native'], a_r=risk['exact_a'], shed=shed,
                native_j=compute_j_trade(record['lambda_r'], risk['native'], shed),
                a_j=compute_j_trade(record['lambda_r'], risk['exact_a'], shed),
                fresh_inference=False, fresh_ops=False, fresh_ac_audit=False)


def goc_comparison(root):
    """FT7 outcomes on each method's own 15 selected decisions, not matched tests.

    State discrepancies compare to the economic Reference A at that method's
    selected topology and service. Missing state normalizations remain NaN.
    """
    import numpy as np
    import pandas as pd
    directory = Path(root) / 'experiments/goc_500/results/refined_study/core_results'
    refs = pd.read_parquet(directory / 'reference_a_all.parquet')
    states = pd.read_parquet(directory / 'state_fidelity_all.parquet')
    native = pd.read_parquet(directory / 'method_finalists_all.parquet')
    rows = []
    for label, method in GOC_METHODS.items():
        r, s = refs.loc[refs.method.eq(method)], states.loc[states.method.eq(method)]
        finite = s.loc[np.isfinite(s.nrmse)]
        rows.append(dict(
            model=label, method=method, finalists=len(r),
            native_j_mean=native.loc[native.method.eq(method), 'j_trade'].mean(),
            ac_j_mean=r.reference_a_j_true.mean(), ac_cost_mean=r.reference_a_objective.mean(),
            state_nrmse_mean=finite.nrmse.mean(), finite_state_families=finite.metric_family.nunique(),
            absolute_risk_discrepancy_mean=(r.native_r_norm - r.reference_a_r_norm_ac).abs().mean(),
            absolute_objective_discrepancy_mean=(r.native_j_trade - r.reference_a_j_true).abs().mean(),
        ))
    return pd.DataFrame(rows)


def texas_validation(root):
    """Physical residuals by checkpoint/distribution; absent checkpoints stay absent.

    GENCO uses its physical evaluator. OpenGridSFM uses the independent physical
    audit, not its native normalized training loss.
    """
    import pandas as pd
    directory = Path(root) / 'experiments/texas2k/results/stage_m/tables'
    data = pd.read_csv(directory / 'physical_validation.csv')
    rows = []
    for (task, distribution), group in data.groupby(['checkpoint_task', 'distribution']):
        family = 'genco_opf' if '.genco_opf.' in task else 'opengridsfm'
        prefix = '' if family == 'genco_opf' else 'independent_'
        rows.append(dict(
            checkpoint_task=task, family=family, distribution=distribution, records=len(group),
            mean_absolute_p_mw=group[prefix + 'mean_abs_p_residual_mw'].mean(),
            mean_absolute_q_mvar=group[prefix + 'mean_abs_q_residual_mvar'].mean(),
            mean_worst_bus_p_mw=group[prefix + 'max_abs_p_residual_mw'].mean(),
            mean_worst_bus_q_mvar=group[prefix + 'max_abs_q_residual_mvar'].mean(),
            metric_source='GENCO physical evaluator' if not prefix else 'independent physical audit',
        ))
    return pd.DataFrame(rows)


def study_coverage(root):
    """Actual retained populations, independent of live scheduler status."""
    import pandas as pd
    root = Path(root)
    goc = root / 'experiments/goc_500/results/refined_study'
    texas = root / 'experiments/texas2k/results/stage_m/tables'
    fits = pd.read_csv(texas / 'fine_tuning_inventory.csv')
    validation = pd.read_csv(texas / 'physical_validation.csv')
    return {
        'goc_500': {
            'study': 'accepted refined FT7', 'methods': list(GOC_METHODS),
            'candidate_rows': len(pd.read_parquet(goc / 'core_results/candidate_evaluations_all.parquet')),
            'reference_a_rows': len(pd.read_parquet(goc / 'core_results/reference_a_all.parquet')),
            'reference_b_rows': len(pd.read_parquet(goc / 'core_results/reference_b_all.parquet')),
            'crossed_warm_start_rows': len(pd.read_parquet(goc / 'core_results/warm_start_crossed.parquet')),
            'rq1_unique_decisions': len(pd.read_parquet(root / 'experiments/goc_500/results/rq1/tables/rq1_paired_runtime.parquet')),
            'full_historical_reexecution_qualified': False,
        },
        'texas2k': {
            'certified_fit_rows': len(fits),
            'locally_retained_validation_checkpoints': validation.checkpoint_task.nunique(),
            'validation_rows': len(validation),
            'completed_genco_searches': len(pd.read_csv(texas / 'finalist_native_and_exact.csv')),
            'completed_native_searches': 0, 'phase_i_complete': False,
            'note': 'Later remote validation status does not supply absent local per-case metrics.',
        },
    }


def texas_historical_comparison(root):
    """Join retained K/L/M A/B endpoints without treating them as controlled trials."""
    import numpy as np
    import pandas as pd
    directory = Path(root) / 'experiments/texas2k/results'
    context = pd.read_csv(directory / 'stage_m/tables/stage_k_l_m_lambda08_context.csv')
    context['selected_service'] = context.selected_service.fillna(1 - context.shed)
    sources = {
        'K': (pd.read_csv(directory / 'stage_k/tables/finalist_native_and_ac_references.csv'),
              {'a_r': 'r_norm_reference_a', 'b_r': 'r_norm_reference_b',
               'maximum_service_fraction': 'maximum_service_fraction'}),
        'L': (pd.read_csv(directory / 'stage_l/tables/finalist_native_and_exact.csv'),
              {'a_r': 'a_r', 'b_r': 'b_r', 'maximum_service_fraction': 'maximum_service_fraction'}),
    }
    for index, row in context.iterrows():
        if row.stage not in sources:
            continue
        source, columns = sources[row.stage]
        matched = source.loc[source.evaluator.eq(str(row.model)) & source.lambda_r.eq(float(row.lambda_r))]
        if len(matched) != 1:
            raise ValueError('historical evaluator/lambda is not unique')
        record = matched.iloc[0]
        if not np.isclose(float(row.a_r), float(record[columns['a_r']]), rtol=1e-10, atol=1e-10):
            raise ValueError('historical Reference A binding differs')
        for target, original in columns.items():
            context.loc[index, target] = record[original]
    return context


def regenerate(root, study, output):
    """Regenerate figures and summary CSVs entirely from included observations."""
    if study not in ('goc_500', 'texas2k'):
        raise ValueError('study must be goc_500 or texas2k')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    root, output = Path(root).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    figures = []

    def save(name, figure):
        figure.tight_layout()
        for extension in ('png', 'pdf'):
            figure.savefig(output / (name + '.' + extension), dpi=150, bbox_inches='tight')
        plt.close(figure)
        figures.append(name)

    if study == 'texas2k':
        from .reporting_metrics import empirical_frontier, topology_incumbent
        directory = root / 'experiments/texas2k/results/stage_m/tables'
        candidates = pd.read_parquet(directory / 'candidate_results.parquet')
        exact = pd.read_csv(directory / 'finalist_native_and_exact.csv')
        labels = list(candidates.model.unique())
        fig, axes = plt.subplots(1, len(labels), figsize=(5 * len(labels), 4.5),
                                 squeeze=False, sharex=True, sharey=True)
        for ax, label in zip(axes[0], labels):
            rows = candidates.loc[candidates.model.eq(label) & candidates.eligible]
            frontier = empirical_frontier(rows)
            ax.scatter(rows.l_shed_total, rows.r_norm, s=8, alpha=.25)
            ax.plot(frontier.l_shed_total, frontier.r_norm, color='black')
            audited = exact.loc[exact.model.eq(label)]
            ax.scatter(audited.shed, audited.a_r, marker='D', label='Economic AC A')
            ax.axhline(1, color='gray', ls=':')
            ax.set(title=label, xlabel='Shed fraction', ylabel='Normalized risk')
            ax.legend()
        fig.suptitle('Evaluated pool at lambda=0.8; only the finalists have AC audits')
        save('empirical_tradeoffs', fig)
        fig, ax = plt.subplots(figsize=(9, 5))
        for label in labels:
            rows = candidates.loc[candidates.model.eq(label)]
            ax.plot(np.arange(1, len(rows) + 1), topology_incumbent(rows), label=label)
        ax.set(xlabel='Topology attempt', ylabel='Best native merit')
        ax.legend()
        save('outer_convergence', fig)
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        x = np.arange(len(exact))
        for ax, column, title in zip(axes, ['a_r', 'a_j', 'a_cost'],
                ['Economic AC A risk', 'Economic AC A tradeoff objective', 'Economic AC A generation cost: case units']):
            ax.bar(x, exact[column])
            ax.set(xticks=x, xticklabels=exact.model, title=title)
            ax.tick_params(axis='x', labelrotation=20)
        save('exact_reference_a', fig)
        exact.to_csv(output / 'regenerated_reference_summary.csv', index=False)
        validation = texas_validation(root)
        validation.to_csv(output / 'regenerated_physical_validation_summary.csv', index=False)
        grid = validation.loc[validation.distribution.eq('G')]
        fig, axes = plt.subplots(1, 2, figsize=(13, 5))
        for ax, family in zip(axes, ['genco_opf', 'opengridsfm']):
            group = grid.loc[grid.family.eq(family)]
            names = group.checkpoint_task.str.replace('v070.' + family + '.', '', regex=False).str.replace('.s0.validation', '', regex=False)
            ax.bar(np.arange(len(group)) - .18, group.mean_absolute_p_mw, width=.36, label='Mean bus |P|')
            ax.bar(np.arange(len(group)) + .18, group.mean_worst_bus_p_mw, width=.36, label='Mean worst-bus |P|')
            ax.set(yscale='log', xticks=np.arange(len(group)), xticklabels=names,
                   title=family + ' / G validation', ylabel='Active power imbalance (MW; log scale)')
            ax.tick_params(axis='x', labelrotation=25)
            ax.legend()
        save('physical_validation', fig)
        context = texas_historical_comparison(root)
        context.to_csv(output / 'regenerated_historical_risk_service.csv', index=False)
        fig, ax = plt.subplots(figsize=(9, 5))
        for row in context.itertuples():
            if not np.isfinite(row.a_r) or not np.isfinite(row.selected_service):
                continue
            label = str(row.model) + ' / ' + str(row.stage)
            point = ax.scatter(100 * row.selected_service, row.a_r, label=label)
            if np.isfinite(row.b_r) and np.isfinite(row.maximum_service_fraction):
                ax.annotate('', (100 * row.maximum_service_fraction, row.b_r),
                            (100 * row.selected_service, row.a_r),
                            arrowprops=dict(arrowstyle='->', color=point.get_facecolor()[0]))
                ax.scatter(100 * row.maximum_service_fraction, row.b_r, facecolors='none', edgecolors=point.get_facecolor())
        ax.scatter([100], [1], marker='*', color='black', s=100, label='Stored baseline')
        ax.set(xlabel='Demand served (%)', ylabel='AC normalized risk', title='Historical A/B endpoints at lambda=0.8; arrows are not feasible frontiers')
        ax.legend(fontsize=8)
        save('historical_risk_service', fig)
        summary = dict(study=study, completed_searches=len(labels), candidate_rows=len(candidates),
                       lambda_values=sorted(candidates.lambda_r.unique().tolist()), phase_i_complete=False,
                       locally_retained_validation_checkpoints=validation.checkpoint_task.nunique())
    else:
        directory = root / 'experiments/goc_500/results'
        data = pd.read_csv(directory / 'ft6_test_metrics.csv')
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        labels = (data.model_id + ' / ' + data.stratum).tolist()
        for ax, column in zip(axes, ['V_mae', 'kcl_P_resid', 'cost_mape']):
            ax.bar(np.arange(len(data)), data[column])
            ax.set(xticks=np.arange(len(data)), xticklabels=labels, title=column)
            ax.tick_params(axis='x', labelrotation=75)
        save('goc500_recorded_physical_evaluation', fig)
        data.to_csv(output / 'regenerated_test_metrics.csv', index=False)
        comparison = goc_comparison(root)
        comparison.to_csv(output / 'regenerated_refined_comparison.csv', index=False)
        fronts = pd.read_parquet(directory / 'refined_study/derived/evaluated_native_pareto_frontiers.parquet')
        fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
        for ax, scenario in zip(axes, ['J-S1', 'J-S2', 'J-S3']):
            for label, method in GOC_METHODS.items():
                group = fronts.loc[fronts.method.eq(method) & fronts.scenario_id.eq(scenario)].sort_values('l_shed_total')
                ax.plot(100 * group.l_shed_total, group.r_norm, label=label)
            ax.axhline(1, color='gray', ls=':')
            ax.set(title=scenario, xlabel='Demand shed (%)', ylabel='Native normalized risk')
            ax.legend()
        fig.suptitle('FT7 empirical frontiers pooled across five lambda searches; not AC-feasible frontiers')
        save('goc500_refined_empirical_frontiers', fig)
        model_rows = comparison.set_index('model').loc[['M0', 'M1', 'M2', 'M3']]
        columns = ['state_nrmse_mean', 'absolute_risk_discrepancy_mean', 'absolute_objective_discrepancy_mean']
        relative = model_rows[columns].div(model_rows.loc['M0', columns])
        relative.to_csv(output / 'regenerated_ac_agreement_relative_to_m0.csv')
        fig, ax = plt.subplots(figsize=(7, 4))
        picture = ax.imshow(relative.to_numpy(dtype=float), cmap='YlGnBu_r', vmin=0, vmax=1, aspect='auto')
        ax.set(xticks=range(3), xticklabels=['State NRMSE', 'Absolute risk\ndiscrepancy', 'Absolute objective\ndiscrepancy'],
               yticks=range(4), yticklabels=relative.index,
               title='Discrepancy from economic AC A / M0 discrepancy (lower is closer)')
        for i in range(4):
            for j in range(3):
                value = float(relative.iloc[i, j])
                ax.text(j, i, f'{value:.2f}', ha='center', va='center', color='white' if value < .4 else 'black')
        fig.colorbar(picture, ax=ax)
        save('goc500_ac_agreement', fig)
        warm = pd.read_parquet(directory / 'refined_study/derived/ipopt_warm_start_summary.parquet')
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.barh(warm.warm_start_label, warm.mean_ipopt_solve_seconds)
        ax.set(xlabel='Mean IPOPT solve time (s; inference/construction excluded)', title='525 controlled same-instance warm-start solves')
        save('goc500_warm_start', fig)
        rq1 = pd.read_parquet(directory / 'rq1/tables/rq1_paired_runtime.parquet')
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
        axes[0].scatter(rq1.m0_evaluator_median_seconds, rq1.refa_evaluator_median_seconds, s=18)
        axes[0].set(xlabel='M0 evaluator median (s)', ylabel='Reference A evaluator median (s)', title='54 unique fixed decisions')
        axes[1].hist(rq1.evaluator_speedup, bins=12)
        axes[1].axvline(rq1.evaluator_speedup.median(), color='black', ls='--')
        axes[1].set(xlabel='Paired AC / M0 evaluator speedup', ylabel='Unique decisions', title=f'Median speedup {rq1.evaluator_speedup.median():.2f}x')
        save('goc500_fixed_decision_runtime', fig)
        summary = dict(study=study, recorded_model_strata=len(data), evaluation_only=True,
                       refined_methods=list(GOC_METHODS), refined_candidate_rows=150000,
                       rq1_unique_decisions=len(rq1), rq1_median_evaluator_speedup=float(rq1.evaluator_speedup.median()),
                       note='GOC FT6 held-out, FT7 selected OPS, and RQ1 timing populations remain distinct; not pooled with Texas2k.')
    summary['figures'] = figures
    summary['fresh_inference'] = summary['fresh_ops'] = summary['fresh_ac_audit'] = False
    (output / 'regeneration.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    return summary
