"""Regenerate published-study figures from included tables, without model imports."""

import json
from pathlib import Path

from .reporting_metrics import empirical_frontier,topology_incumbent


def recompute_retained_decision(root,regime,*,family='genco_opf'):
    """Check a stored finalist from derived branch diagnostics; no new prediction."""
    from .objectives import compute_r_norm,compute_l_shed,compute_j_trade
    if regime not in ('G500','G100_to_R400','G100_to_W400') or family not in ('genco_opf','opengridsfm'):
        raise ValueError('unknown completed model regime')
    name=regime if family=='genco_opf' else family+'_'+regime
    path=Path(root)/'experiments/texas2k/results/stage_m/retained_decisions'/(name+'.json')
    record=json.loads(path.read_text())
    mappings={name:{int(k):float(v) for k,v in record[name].items()}
        for name in ('alpha','p_env','pd_normalized_weights','native_loading','exact_a_loading')}
    shed=compute_l_shed(mappings['pd_normalized_weights'],mappings['alpha'])
    risk={state:compute_r_norm(mappings['p_env'],record['offline_branch_ids'],mappings['p_env'],
        mappings[state+'_loading'],record['r_base']) for state in ('native','exact_a')}
    return dict(model=record['model'],offline_branch_ids=record['offline_branch_ids'],
        native_r=risk['native'],a_r=risk['exact_a'],shed=shed,
        native_j=compute_j_trade(record['lambda_r'],risk['native'],shed),
        a_j=compute_j_trade(record['lambda_r'],risk['exact_a'],shed),
        fresh_inference=False,fresh_ops=False,fresh_ac_audit=False)


def regenerate(root,study,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    root,output=Path(root).resolve(),Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    figures=[]
    def save(name,figure):
        figure.tight_layout()
        for extension in ('png','pdf'):figure.savefig(output/(name+'.'+extension),dpi=160,bbox_inches='tight')
        plt.close(figure);figures.append(name)
    if study=='texas2k':
        directory=root/'experiments/texas2k/results/stage_m/tables'
        candidates=pd.read_parquet(directory/'candidate_results.parquet')
        exact=pd.read_csv(directory/'finalist_native_and_exact.csv')
        labels=list(candidates.model.unique())
        fig,axes=plt.subplots(1,len(labels),figsize=(5*len(labels),4.5),squeeze=False,sharex=True,sharey=True)
        for ax,label in zip(axes[0],labels):
            rows=candidates.loc[candidates.model.eq(label)&candidates.eligible]
            frontier=empirical_frontier(rows)
            ax.scatter(rows.l_shed_total,rows.r_norm,s=8,alpha=.25)
            ax.plot(frontier.l_shed_total,frontier.r_norm,color='black')
            audited=exact.loc[exact.model.eq(label)]
            ax.scatter(audited.shed,audited.a_r,marker='D',label='Economic AC A')
            ax.axhline(1,color='gray',ls=':');ax.set(title=label,xlabel='Shed fraction',ylabel='Normalized risk');ax.legend()
        fig.suptitle('Empirical evaluated pool, lambda0.8 only; not a global Pareto frontier')
        save('empirical_tradeoffs',fig)
        fig,ax=plt.subplots(figsize=(9,5))
        for label in labels:
            rows=candidates.loc[candidates.model.eq(label)]
            ax.plot(np.arange(1,len(rows)+1),topology_incumbent(rows),label=label)
        ax.set(xlabel='Topology attempt',ylabel='Best native merit');ax.legend();save('outer_convergence',fig)
        fig,axes=plt.subplots(1,3,figsize=(15,5));x=np.arange(len(exact))
        for ax,column,title in zip(axes,['a_r','a_j','a_cost'],['Economic AC A risk','Economic AC A tradeoff objective','Economic AC A generation cost: case units']):
            labels=[name.replace('GENCO ','GENCO\n').replace('OpenGridSFM ','OpenGrid\nSFM\n').replace(' -> ',' ->\n') for name in exact.model]
            ax.bar(x,exact[column]);ax.set(xticks=x,xticklabels=labels,title=title)
            ax.tick_params(axis='x',labelsize=8)
        save('exact_reference_a',fig)
        exact.to_csv(output/'regenerated_reference_summary.csv',index=False)
        summary=dict(study=study,completed_searches=len(labels),candidate_rows=len(candidates),
                     lambda_values=sorted(candidates.lambda_r.unique().tolist()),phase_i_complete=False)
    else:
        data=pd.read_csv(root/'experiments/goc_500/results/ft6_test_metrics.csv')
        fig,axes=plt.subplots(1,3,figsize=(15,5))
        labels=(data.model_id+' / '+data.stratum).tolist()
        for ax,column in zip(axes,['V_mae','kcl_P_resid','cost_mape']):
            ax.bar(np.arange(len(data)),data[column]);ax.set(xticks=np.arange(len(data)),xticklabels=labels,title=column);ax.tick_params(axis='x',labelrotation=75)
        save('goc500_recorded_physical_evaluation',fig)
        data.to_csv(output/'regenerated_test_metrics.csv',index=False)
        summary=dict(study=study,recorded_model_strata=len(data),evaluation_only=True,
                     note='Historical recorded GOC-500 populations; not pooled with Texas2k errors')
    summary['figures']=figures
    (output/'regeneration.json').write_text(json.dumps(summary,indent=2))
    return summary
