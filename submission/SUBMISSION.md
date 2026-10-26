# GENCO in the Loop: From Grid Adaptation to Wildfire-Aware Power Shutoff

**Caleb Lu and Xiao Liu** · H. Milton Stewart School of Industrial and Systems Engineering, Georgia Institute of Technology

**[Repository and reproducible demos](https://github.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff)** · **[GENCO and GridSFM checkpoints](https://github.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/releases/tag/phase-i-models-v152)** · **[Three-page technical submission](https://github.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/blob/main/submission/GENCO_Challenge_Submission.pdf)**

## Why OPS is a useful testbed for grid foundation models

Wildfire-aware **Optimal Power Shutoff (OPS)** aims to reduce exposure from energized transmission lines while retaining electricity service. Following Rhodes, Ntaimo, and Roald (2021), we investigate a predict-then-optimize workflow that proposes line de-energizations, adjusts selected load-service controls, evaluates the resulting operating states, and finally checks selected decisions using **nonlinear AC physics**. This is a combinatorial task: changing one line can redistribute flow throughout the network.

**Our central question is not only whether a model predicts a grid state accurately, but whether its predictions lead to better *AC-verified operational decisions*.** We first established the workflow on GOC-500 using **GridSFM**, then transferred it to a modified Texas2k system using **GENCO-OPF**, real weather-derived exposure, and grid-to-task fine-tuning.

Before using a learned evaluator, the **original OPS formulation** from Rhodes et al. weighs **served demand against wildfire exposure** while enforcing component and power-flow constraints. Our computationally bounded version expresses the same central preference as
```text
Minimize  J = λR × normalized wildfire exposure + (1 − λR) × load shedding
Decisions: line status z; requested load service α; generation response under the evaluator's control contract
```
The original OPS co-optimizes network decisions and operational recourse using a DC formulation. **Our application differs:** we first propose topologies, then use a learned electrical-state evaluator with a bounded load-service search, and finally run nonlinear AC audits. This is a *screen-and-verify heuristic*, not a claim of replacing the exact constrained OPS formulation.

![Original OPS formulation versus our surrogate-assisted screening](https://raw.githubusercontent.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/main/submission/figures/00_ops_original_to_surrogate.svg)

![Surrogate-assisted OPS and AC-verification workflow](https://raw.githubusercontent.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/main/submission/figures/01_workflow.png)

The current evaluator screens candidate topologies with at most **two planned shutoffs**, followed by a bounded five-load-control search with up to **20 model objective calls per topology**. Exact AC Reference A fixes topology and requested service, then optimizes economic dispatch. Reference B1/B2 asks how much service that topology can physically deliver, followed by an economic tie-break. These are **audits of selected solutions**, not global optimality certificates or risk-constrained corrective OPF.

## 1. GOC-500: a controlled laboratory for adaptation and downstream decisions

We began with **three constructed diagnostic hazard patterns**: a high-risk line with low service consequences, one with high service consequences, and one with an alternate network path. These interpretable cases allowed us to establish the topology-proposal → GridSFM state evaluation → recourse → AC-reference workflow before introducing geographic hazard data.

We compared the released GridSFM checkpoint **M0** with **M1** (1,000 intact-grid cases), **M2** (M1 plus 500 intact cases), and **M3** (M1 plus 500 N−1 cases). Across a common **375 intact + 375 N−1 held-out test**, M2 had the lowest intact loss and M3 the lowest N−1 loss. Intact active branch-flow MAE fell from **0.0745 p.u. (M0)** to **0.0350 p.u. (M2)**.

Fine-tuning convergence is recorded across ten epochs of additional intact-versus-N−1 adaptation. The two continuation paths trade off intact and contingency accuracy; this is not uniform improvement in every physical metric.

![GOC-500 N−1 validation loss during sequential adaptation](https://raw.githubusercontent.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/main/submission/figures/04_goc_n1_validation_convergence.svg)

*GOC-500 convergence on a common N−1 validation split: ten-epoch continuation from M1 with either 500 additional intact cases (M2) or 500 N−1 cases (M3). This is training/validation convergence, not OPS-search convergence. [Source traces](https://github.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/blob/main/experiments/goc_500/results/ft6_training_trajectories.csv).*

![GOC-500 fine-tuning agreement and measured screening speed](https://raw.githubusercontent.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/main/submission/figures/03_goc_evidence.png)

### A concrete OPS result under designed hazard: J-S1

The J-S1 diagnostic assigns elevated exposure to a target line whose removal has relatively low expected service consequence. On the **surrogate-evaluated** J-S1 risk–service frontier, the released GridSFM has normalized risk near **0.47** with zero shedding, while intact-adapted M2 reaches roughly **0.42** with negligible shedding. This illustrates the opportunity for **selected K≤2 de-energizations** to reduce the *predicted* exposure in controlled scenarios. It is **not** a certified exact-AC reduction, nor does the gap isolate topology choice from model calibration and load-service recourse.

![J-S1 exact empirical GridSFM risk–service comparison](https://raw.githubusercontent.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/main/submission/figures/05_goc_j_s1_pareto_illustration.svg)

*J-S1 empirical GridSFM-evaluated Pareto frontier from the original research figure, traced from the supplied source PDF. The plot records native predictions, not certified exact AC reductions. [Retained GOC Pareto evidence](https://github.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/blob/main/experiments/goc_500/results/refined_study/derived/evaluated_native_pareto_frontiers.parquet).*

The strongest lesson came from comparing model predictions with **exact AC-recovered decisions**. For M2 versus M0, mean state NRMSE fell **42%** and absolute risk discrepancy fell **76%**, yet mean AC-audited OPS objective improved by only **about 1.1%**; M1 attained the best mean audited objective. Thus, substantial prediction gains did not translate proportionally into decision gains. The completed GOC study also includes [empirical risk–service frontiers](https://github.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/tree/main/experiments/goc_500/results/refined_study/derived), fixed-decision reference comparisons, and a 525-solve warm-start study.

**Computational evidence:** on **54 matched fixed decisions**, released GridSFM achieved a **3.59× paired-median complete state-evaluation speedup** versus AC-OPF/IPOPT on the tested CPU environment (95% bootstrap interval **3.48–3.68**). A separate warm-start comparison showed only modest solver-time benefits. These are *specific evaluation boundaries*, not whole-OPS or GENCO/Texas2k acceleration figures.

## 2. Texas2k: geographic wildfire exposure reveals a harder problem

We then moved to **modified Texas2k (2,751 buses, 5,344 branches)**, using operating **Scenario 16** and the weather-derived **June 23, 2023, 4:00 PM CDT** wildfire-exposure snapshot. Unlike the designed GOC diagnostics, the geographic exposure is not constructed to guarantee an obvious or favorable shutoff decision. Our loading-dependent risk is an **exposure proxy**, not a calibrated ignition probability, and the synthetic electrical network is not a utility operating study.

The Stage K comparison screened candidate states with **GridSFM, DC, and exact AC**. Its smoke-benchmark-based extrapolation estimated **4.34 hours of serial GridSFM screening on V100 versus 51.47 hours for AC on CPU**, approximately **11.9×** for the tested configuration. This is a **projected hardware-dependent screening comparison**, not a measured GENCO speedup or full end-to-end OPS advantage.

**The contrast with J-S1 is central:** in our GOC diagnostic, high-risk line selection offered clear *surrogate-evaluated* risk reductions at very limited shedding. In the geographic Texas2k snapshot, taking out two lines by itself is not enough to ensure a risk reduction under exact AC conditions. Meaningful decreases in the historical DC/AC comparisons are accompanied by much more aggressive **continuous load-service and dispatch recourse**.

More importantly, **the continuous operating decision often dominates the result in this scenario**. At λR = 0.8, historical DC and AC selected operating points achieved audited normalized risks **0.488 and 0.474**, but with **43.76% and 34.61% load shedding** respectively. Their Reference B recovery can restore essentially full service, although the risk increases to **1.100 and 1.084**. Consequently, opening attractive lines is not sufficient: how generation and service are reoptimized under exact physics matters greatly. These historical methods have broader dispatch and service recourse than our GENCO-OPF wrapper, so this is not a hardware- or control-matched ranking.

![Texas2k incumbent surrogate-search convergence](https://raw.githubusercontent.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/main/experiments/texas2k/results/stage_m/figures/convergence/topology_incumbent.png)

*Texas2k topology-search convergence is a record of the best **native** OPS merit found as candidates are evaluated; it is not convergence to a certified global or AC-feasible optimum.*

For comparable additional context, see the [Texas Stage K/L/M exact reference comparison](https://github.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/blob/main/experiments/texas2k/results/stage_m/figures/stage_k_l_m_comparison/lambda08_exact_reference_context.png) and [empirical native risk–service frontiers](https://github.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/blob/main/experiments/texas2k/results/stage_m/figures/pareto/empirical_native_frontiers.png). Native DC, AC, GridSFM, and GENCO methods do not share identical control freedom or prediction physics; exact references are the more meaningful outcome comparison.

## 3. GENCO-OPF: fine-tune to the grid, then to the operational topology distribution

With the same **500-example total training budget**, we evaluated three GENCO-OPF adaptations:

| Final checkpoint | Adaptation data | What it tests |
|---|---|---|
| **G500** | 500 intact-grid cases | Target-grid adaptation |
| **G100 → R400** | 100 intact + 400 random N−1/N−2 cases | Generic contingency exposure |
| **G100 → W400** | 100 intact + 400 wildfire-ranked N−1/N−2 cases | Task-relevant outage exposure |

The wildfire-ranked cases are **not** AC-OPS-optimal labels. Each final checkpoint screened **301 topologies and 6,020 surrogate objective calls**, sharing the initial 50 single-line candidates while generating model-specific double-outage candidates from the five top-ranked parents. We evaluated held-out G/R/W validation strata and exact AC references for each selected finalist.

![GENCO physical validation and selected-decision audit](https://raw.githubusercontent.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/main/submission/figures/02_texas_evidence.png)

The validation results show mixed transfer. On the intact G stratum, average active-power imbalance remains roughly **51–52 MW per bus**, while sequential adaptation lowers average reactive imbalance from **20.6** to about **16.6–16.7 MVAr**. However, mean *worst-bus* active imbalance increases from **6,265 MW** (G500) to **9,312/9,841 MW** (R/W). Such neural states **cannot be called AC feasible**.

The selected decisions reveal an even more instructive inversion:

| Checkpoint | Selected outage pair | Native OPS objective J ↓ | Audited Reference A J ↓ | Audited risk ↓ |
|---|---|---:|---:|---:|
| **G500** | 117;1548 | **1.0166** | 0.9319 | 1.1641 |
| **G→R** | 117;281 | 1.1601 | **0.8713** | **1.0890** |
| **G→W** | 117;281 | 1.2091 | 0.8714 | 1.0891 |

**G500 looks best under its native score; contingency-adapted checkpoints look better after AC economic recovery.** Both R and W choose the same outage pair and give almost identical audited results. All three audited risks remain **above the stored intact-risk baseline of 1**, so this is *not* a demonstrated operational wildfire-risk reduction. Because the K2 search pools differ and the AC references replace predicted dispatch, this inversion is **not** a common-candidate ranking test or a causal estimate of the benefit of specific training examples.

The difference from GOC-500 is revealing. In constructed diagnostics, selected topology changes can produce clear exposure reductions; on this Texas snapshot, **continuous recourse and AC recovery largely determine the risk–service outcome**. The model's prediction accuracy, operating control interface, candidate search coverage, and exact AC feasibility all become critical.

## 4. What this opens up

**Near term:** Because the Texas experiments reveal the limits of extensive continuous surrogate optimization at each topology, we propose separating broad discrete screening from accurate physical recourse: screen a much larger set of candidate topology decisions cheaply, use GENCO to shortlist promising choices, then solve **risk-aware AC recourse** only for the finalists and rerank using exact outcomes. This is a *proposed extension*, not the method that generated the reported results. Evaluate decision recall, ranking disagreement, AC objective gaps, service recovery, and *whole-workflow* runtime against DC/AC benchmarks at matched control budgets.

**Adaptation study:** expand grid-only and task-only learning curves, test how many intact versus contingency samples to allocate, and examine transfer as planned shutoff budgets move beyond K≤2 to K=5, 10, or 20. These are prospective investigations, not security guarantees.

**Broader view:** grid foundation models can become reusable components of scientific decision workflows: **simulate → generate evidence → adapt → screen → physically verify**. This study illustrates the need for that verification layer rather than claiming deployment-ready autonomy.

## Reproduce and build on the work

**[Repository](https://github.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff)** · **[Documentation and reproduction guide](https://github.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/blob/main/docs/reproduction.md)** · **[Public model archives](https://github.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/releases/tag/phase-i-models-v152)** · **[GOC-500 technical supplement](https://github.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/blob/main/submission/supplementary/GOC500_technical_report.pdf)**

The release includes model selectors, certified weights, GOC-500/Texas result tables, and four notebooks. It provides a real public IEEE-14 GENCO interface example with `genco-ops public-genco --output outputs/public_genco --execute`, and regenerates figures from retained compact evidence **without PACE**. Exact modified Texas electrical inputs remain private, so this is not a public full Texas2k rerun. GridSFM is the GOC-500 precursor; GENCO-OPF is the Texas2k challenge experiment. Native fine-tuned GridSFM Texas OPS/AC was pending in the published evidence cut.

**References:** [Rhodes, Ntaimo & Roald, 2021](https://doi.org/10.1109/TPWRS.2020.3046796) · [GENCO (Puech et al., 2026)](https://arxiv.org/abs/2608.09921) · [GridSFM](https://www.microsoft.com/en-us/research/publication/gridsfm-a-foundation-model-for-ac-optimal-power-flow/).
