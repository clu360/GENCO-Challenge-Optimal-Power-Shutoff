# GENCO in the Loop

**Grid-to-task adaptation and physical verification for wildfire-aware power shutoff**  
**Caleb Lu and Xiao Liu** · H. Milton Stewart School of Industrial and Systems Engineering, Georgia Institute of Technology  
Contact: [clu360@gatech.edu](mailto:clu360@gatech.edu) (primary); [xiao.liu@isye.gatech.edu](mailto:xiao.liu@isye.gatech.edu)

## Summary

How does adapting a grid foundation model change the quality of decisions made with it? We develop a downstream testbed for **GENCO-OPF**, using wildfire-aware optimal power shutoff (OPS) to connect prediction fidelity, topology screening, and exact AC verification. On a modified Texas2k grid, three adaptations trained on 500 examples select decisions with AC-audited normalized risks of **1.164, 1.089, and 1.089**. The contingency-adapted checkpoints select lower-risk, lower-shedding decisions in this case, yet all remain above the stored baseline. Together with a GridSFM precursor on GOC-500, these mixed results reveal why adaptation, control flexibility, and physical verification must be evaluated together.

## Motivation and method

OPS trades reduced wildfire exposure against interrupted service [1]. Repeated electrical-state evaluations make a reusable predictor attractive. GENCO's graph representation and GraphKit implementation [2] let us adapt an existing checkpoint and evaluate changed topology and demand. Its OPF interface also shapes the downstream problem: it predicts dispatch from its inputs; our wrapper does not expose arbitrary generator commands or condition the model directly on a wildfire objective.

For energized-line indicators **z** and served-demand fractions **α**, we report **J = λR Rnorm + (1 − λR) Lshed**. Rnorm sums environmental exposure × squared apparent-power loading over energized transmission risk lines, divided by the stored intact-grid risk; Lshed is the unserved demand fraction. This is a loading-dependent exposure proxy, not a calibrated ignition probability. Evaluators retain their declared physics penalties separately from J.

![Figure 1. GENCO adaptation and verification workflow.](figures/01_workflow.png)

*Figure 1. Completed work adapts GENCO, screens bounded topology/service choices, and audits selected decisions. Broader screening followed by risk-aware AC refinement and reranking is the proposed extension.*

Both studies permit at most two shutoffs. Each surrogate searches five topology-relevant load-service controls with at most 20 evaluations per topology. **Reference A** fixes topology and service, then minimizes AC generation cost. **B1/B2** maximize AC-feasible total service and then minimize cost at that service; the Texas policy relaxes online generator P minima to zero. B imposes no wildfire-risk constraint. These nonlinear solves provide local operating points, not global optimality certificates. Our research question is whether improved surrogate diagnostics survive this change from predicted to AC-recovered states.

<!-- pagebreak -->

## GENCO on Texas2k: what task adaptation changes

We study target-grid adaptation under geographic wildfire exposure: one frozen operating case, load Scenario 16, and the June 23, 2023, 16:00 CDT weather-hazard snapshot. The modified synthetic system has 2,751 buses and 5,344 branches. It differs from the official GENCO Texas grid; this is not utility operational validation or demonstrated cross-region transfer.

**A matched adaptation budget.** G500 uses 500 intact-grid examples. G→R and G→W each use 100 intact examples followed by 400 random or wildfire-ranked outage examples. W samples risk-ranked outages, not optimal OPS labels. We compare these three adapted GENCO-OPF checkpoints at equal total sample counts; this is not a matched test of improvement over the released checkpoint.

![Figure 2. GENCO validation across distributions and exact selected-decision outcomes.](figures/02_texas_evidence.png)

*Figure 2. Left: mean bus-level absolute P/Q imbalance on 100 cases per validation distribution (MW/MVAr; lower is better). Right: Reference A outcomes at λR = 0.8. G→R and G→W select the same outage pair, 117;281; G500 selects 117;1548. Branch identifiers are local indices.*

**Average fidelity and extremes tell different stories.** On G validation, mean P imbalance is similar across final checkpoints (51–52 MW). Sequential adaptation lowers mean Q imbalance from 20.6 to about 16.6–16.7 MVAr. On wildfire validation, G→W has the lowest mean P imbalance (52.3 versus 55.8 and 57.8 MW). However, mean worst-bus P imbalance on G validation increases from **6,265 MW** for G500 to **9,312/9,841 MW** for G→R/W. These predictions must not be treated as AC-feasible states.

**Training distribution changes the selected decision, with limited evidence of benefit.** Each search evaluates 301 topologies and 6,020 objective calls: intact, 50 common single outages, and 250 pairs drawn from five evaluator-ranked parents. Sequential adaptations select lower Reference A risk and less shedding than G500 (Figure 2), but their common pair and nearly identical outcomes do not distinguish R from W. Model-dependent pair generation also couples evaluation and search coverage. All audited risks exceed baseline 1; economic redispatch against a stored baseline does not isolate the causal effect of shutoffs.

**Continuous recourse exposes a distinct tradeoff.** Historical Texas DC/AC searches obtain Reference A risk 0.488/0.474 while shedding 43.76%/34.61%. B restores essentially full service but raises risk to 1.100/1.084. For GENCO's selected pairs, B also restores full service, at risk 1.172 (G500) and 1.096 (G→R/W). Thus maximum service does not preserve the lower-risk operating point. The historical optimizers freely adjust dispatch and service, so their gap from GENCO mixes control freedom, fidelity, and search coverage. Eight Texas fits across both model families are certified; native GridSFM OPS/AC remains pending in this evidence cut.

<!-- pagebreak -->

## GOC-500 precursor: fidelity gains exceed decision gains

The precursor uses **GridSFM, not GENCO** [3], on three constructed hazard patterns, five λR values, and 100 topology attempts from shared frozen pools per setting. Released M0 is compared with M1 (1,000 intact examples), M2 (M1 + 500 intact), and M3 (M1 + 500 N−1). A common test population contains 375 intact and 375 N−1 cases. M2 has the lowest intact-case loss; M3 has the lowest N−1 loss. Intact branch-P MAE falls from 0.0745 p.u. (M0) to 0.0350 (M2).

![Figure 3. GOC-500 fidelity and fixed-decision timing evidence.](figures/03_goc_evidence.png)

*Figure 3. Left: mean state-family NRMSE and absolute native-to-A risk/objective discrepancies at each model's own selected decisions across 15 common settings, divided by the corresponding M0 value. Lower means less error, not a feasibility rate. Right: a separate 54-decision CPU benchmark of released M0; displayed medians are not the paired speedup estimator.*

M2 reduces state NRMSE by 42% and risk discrepancy by 76%, yet mean AC-audited J improves only about 1.1% versus M0; M1 has the best mean audited J. At λR = 0.8, M1's audited risks are 0.394, 0.945, and 0.448 with about 0.93% shedding, already close to M0. Prediction improvements therefore need not yield comparable decision improvements. Constructed GOC hazards and geographic Texas exposure also have different risk concentration; their reduction magnitudes are not directly comparable.

The paired CPU benchmark finds **3.59× median speedup** for complete M0 state evaluation versus fixed-decision AC-OPF (95% bootstrap interval 3.48–3.68). Startup, downstream scoring, and publication I/O are excluded. A separate 525-solve warm-start study finds only 2.2% lower mean IPOPT time for M2, excluding inference. Neither measurement establishes GENCO/Texas end-to-end acceleration.

## Lessons, next steps, and reproducibility

The contribution is a testbed that exposes the interaction between **adaptation distribution, physical fidelity, control interface, and audited decision quality**. We propose broader, shallow topology screening followed by risk-aware AC refinement of a shortlist. Future tests will measure top-N recall, rank agreement, audited objective gaps, and total runtime under matched control budgets. Increasing the shutoff budget and increasing candidate coverage are separate experiments; this extension is not yet implemented.

The repository provides 15 selectable checkpoint entries, retained result tables, four notebooks, and a small public IEEE-14 **GENCO compatibility demo**. That demo establishes a runnable loading/evaluation path, not reproduction of Texas performance. All three figures and this PDF rebuild from included compact tables without private inputs or PACE. Exact modified Texas electrical inputs remain private; public weather-derived exposure is included. The exact GOC test-population hashes and official acquisition recipe are provided, but its full 750-case replay has not been reverified. Full historical OPS/AC recomputation remains a separate task.

**Resources.** [Public code, notebooks, results, and data coverage](https://github.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff) · [Public checkpoint archives](https://github.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/releases/tag/phase-i-models-v152) · [GOC technical supplement](supplementary/GOC500_technical_report.pdf). Repository and model-download access are verified without authentication; exact Texas electrical inputs remain private. The accompanying availability note supersedes the supplement's earlier “upon acceptance” statement.

**References.** [1] [Rhodes, Ntaimo & Roald, *Balancing Wildfire Risk and Power Outages Through Optimized Power Shut-Offs*, 2021](https://doi.org/10.1109/TPWRS.2020.3046796). [2] [Puech et al., *GENCO*, 2026](https://arxiv.org/abs/2608.09921) and [OpenGridFM GraphKit](https://github.com/gridfm/gridfm-graphkit). [3] [Yang et al., *GridSFM: A Foundation Model for AC Optimal Power Flow*, 2026](https://www.microsoft.com/en-us/research/publication/gridsfm-a-foundation-model-for-ac-optimal-power-flow/).
