# Methodology

## Research question and separate studies

The GENCO contribution is a downstream testbed for target-grid/task adaptation
and physical verification: does changing an evaluator's training distribution
improve its predictions and the AC-audited decisions selected with it? The
completed experiments measure those links separately. Broader shallow screening
followed by risk-aware AC shortlist refinement remains a proposed extension.

GOC-500 Stage J examines native GridSFM adaptation. FT0 is a ten-case smoke
checkpoint. M1 uses 1,000 intact-grid examples; M2 and M3 are sibling adaptations
from M1 using 500 intact and 500 N-1 examples respectively. Each stage used ten
epochs. FT6 compares M0/M1/M2/M3 on the same sealed 375-FullTop plus 375-N-1 test
graphs. The exact ordered fingerprints and official acquisition recipe are in
[`evaluation_population.json`](../experiments/goc_500/data/evaluation_population.json);
the 750-case numerical replay has not been reverified in this release.

The completed refined FT7 OPS study compares DC and M0/M1/M2/M3 across three
constructed hazard scenarios and five risk weights. It reuses hash-bound DC,
M0 and M1 evidence from the earlier campaigns and adds the M2/M3 searches. Each
setting uses 100 topology attempts from common frozen pools and at most 20
continuous evaluations per attempt. At lambda zero a pool has 99 unique topology
identifiers; an attempt budget is not a count of unique physical topologies.
FT7 includes selected-decision A/B audits and a controlled 525-solve crossed
warm-start study. A separate 54-decision RQ1 benchmark measures released-M0
evaluation time against fixed-decision AC-OPF. These timing boundaries differ.
The public 500-bus sample used for a new bounded demo is neither the FT6 test
population nor a replay of the full FT7 search.

Texas2k Phase I compares GENCO-OPF and OpenGridSFM. Both use shared accepted
economic AC-OPF labels, grouped splits and the same physical examples. Each
family has G100, G500, G100-to-R400 and G100-to-W400 fits; G100 is an intermediate,
not a final OPS representative. Sequential variants use 100 Grid plus 400 task
examples, not 500 Grid plus 400 task examples. W denotes wildfire-ranked eligible
topologies, not imitation of globally optimal continuous AC-OPS decisions. The
raw validation code `O` denotes this W distribution; `R` denotes random outages.
The retained GENCO validation summaries use 100 cases per distribution and
checkpoint. Validation diagnostics are separate from the selected OPS states.

Eight Texas fits are certified, including the two intermediate G100 checkpoints.
The publication cut contains completed OPS/A/B evidence for the three final
GENCO models. Native GridSFM OPS/A/B remains pending. GOC-500 is a GridSFM
precursor, not an evaluation of GENCO on that grid or a matched cross-grid trial.

## Electrical Contracts

GENCO-OPF predicts an economically dispatched state from topology and demand;
GENCO-PF predicts a state conditional on prescribed generator commands and voltage
controls. Historical Stage L PF transfer/contingency models are not new Phase I
fine-tunes. Their limited redispatch exploration remains a historical limitation.
Phase I downstream controls are alpha-only: five selected load-service controls
per topology, with other requested service fractions at one and source-less
island loads forced to zero. Dispatch is supplied by the OPF predictor; arbitrary
generator commands are not exposed to the GENCO-OPF search. Historical direct
DC/AC optimizers have broader continuous control. Their decision-quality gap
therefore mixes control freedom, model fidelity and search policy. The earlier
proposed redispatch-first Stage M PF search is not the accepted Phase I search.

Models retain their official graph preprocessing and normalization. GENCO uses
GraphKit at the pinned commit. Native GridSFM uses its pinned official package
with the separately versioned exact-impedance FP64 KCL loss overlay exported in
`src/genco_ops/gridsfm_mixed_loss_v015.py`. Its model remains FP32. Canonical AC
target acceptance is distinct from mandatory rounded-FP32 residual diagnostics.
The exported adapter is not claimed to be unmodified upstream training code.

## Wildfire-Aware Search And Audits

The loading-dependent exposure term sums environmental score times squared
apparent loading over energized transmission risk lines. AC loading uses the
larger of the two terminal apparent powers divided by the line rating. Texas
normalization uses the stored Scenario-16 baseline, not a newly optimized intact
economic dispatch; GOC uses its own frozen scenario risk denominators. The
environmental score is not a calibrated ignition probability. This extends the
risk representation of the original OPS formulation, not its exact reproduction.

The reported tradeoff is `J = lambda * R_norm + (1-lambda) * L_shed`.
Declared physics/model penalties contribute to the evaluators' search merit
separately from this reported quantity. A lower plotted J is not an AC-feasibility
certificate, and architectures' raw training losses are not comparable metrics.

Texas Phase I uses lambda 0.8, K0 + 50 K1 + up to 250 K2, five ranked K1 parents,
the original eligibility/tie/deduplication rules, and at most twenty actual alpha
objective calls per topology. The common K1 pool supports a shared comparison;
evaluator-ranked parents can produce different K2 pools. The completed GENCO
searches contain 301 topology states and 6,020 calls each. More candidate coverage
at fixed K and a larger shutoff budget are distinct interventions.

Reference A fixes topology and per-load service and solves economic AC-OPF; it
does not preserve a wildfire-aware dispatch or minimize wildfire risk. B1
maximizes delivered demand at fixed topology. B2 minimizes economic cost subject
to B1's total-service floor, within the declared MW tolerance; its per-load
allocation may differ. The retained Texas B policy sets online-generator active
lower bounds to zero and retains nonnegative upper bounds. It is a maximum-service
reference under that policy, not an identical-bound redispatch of A.

Neither B stage imposes a wildfire-risk ceiling. A/B endpoints do not establish
the full risk-service frontier or rule out more service at A's risk. A legitimate
B2 failure preserves B1 service/diagnostics with economic cost unavailable; B1
failure cannot certify service. Solver success remains subject to physical quality
checks, and local nonlinear solves are not global optimality proofs.

## Reporting

Empirical frontiers, best-so-far topology curves and rank/overlap definitions are
exported directly from Stage L in `reporting_metrics.py`. Spearman can be undefined
under the retained all-shared-K1 definition; it is not silently replaced by zero.
Phase I's empirical frontier is only within the evaluated lambda-0.8 pool.
GOC native-to-A agreement averages each model's own selected operating decisions
at 15 common settings, rather than identical operating inputs. Closer agreement
does not by itself mean a better audited objective. The separate matched FT6
population addresses prediction fidelity on common held-out inputs.
Validation is not an independent confirmatory test. Historical K/L comparisons
share some input identities but differ in search/control/physics/timing details;
they are explicitly only partially comparable.

## Verified References

- Puech et al. (2026), *GENCO - A Unified Neural Solver Embedded in a Development
  Framework for Steady-State Grid Analysis*, [arXiv:2608.09921](https://arxiv.org/abs/2608.09921).
- [Microsoft GridSFM official source](https://github.com/microsoft/GridSFM) and
  [released model](https://huggingface.co/microsoft/GridSFM_Open).
- [GENCO-OPF checkpoint](https://huggingface.co/gridfm/genco-opf-datakit) and
  [official GraphKit framework](https://github.com/gridfm/gridfm-graphkit).
- [PowerModelsWildfire.jl](https://github.com/WISPO-POP/PowerModelsWildfire.jl),
  original OPS implementation context. Security-constrained extension: Rhodes,
  Coffrin and Roald (2024), *Security-constrained optimal power shutoff for
  wildfire risk mitigation*, IET GTD 18(18), 2972-2986,
  [DOI:10.1049/gtd2.13246](https://doi.org/10.1049/gtd2.13246).

Phase II scaling, higher-K switching and new optimization schemes are future work
under this release. Phase II is held.
