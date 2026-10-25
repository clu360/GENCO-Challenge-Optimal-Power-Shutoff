# Methodology

## Separate Studies

GOC-500 Stage J examines native GridSFM adaptation. FT0 is a ten-case smoke
checkpoint. M1 uses 1,000 intact-grid examples; M2 and M3 are sibling adaptations
from M1 using 500 intact and 500 N-1 examples respectively. Each stage used ten
epochs. Retained FT3/FT4 search and FT6 physical-evaluation tables are historical
evidence. The official 500-bus sample included for a new demo is not that test set.

Texas2k Phase I compares GENCO-OPF and OpenGridSFM. Both use shared accepted
economic AC-OPF labels, grouped splits and the same physical examples. Each
family has G100, G500, G100-to-R400 and G100-to-W400 fits; G100 is an intermediate,
not a final OPS representative. Sequential variants use 100 Grid plus 400 task
examples, not 500 Grid plus 400 task examples. W denotes wildfire-ranked eligible
topologies, not imitation of globally optimal continuous AC-OPS decisions.

## Electrical Contracts

GENCO-OPF predicts an economically dispatched state from topology and demand;
GENCO-PF predicts a state conditional on prescribed generator commands and voltage
controls. Historical Stage L PF transfer/contingency models are not new Phase I
fine-tunes. Their limited redispatch exploration remains a historical limitation.
Phase I downstream controls are alpha-only. Do not substitute the earlier proposed
redispatch-first Stage M PF search for the accepted Phase I search.

Models retain their official graph preprocessing and normalization. GENCO uses
GraphKit at the pinned commit. Native GridSFM uses its pinned official package
with the separately versioned exact-impedance FP64 KCL loss overlay exported in
`src/genco_ops/gridsfm_mixed_loss_v015.py`. Its model remains FP32. Canonical AC
target acceptance is distinct from mandatory rounded-FP32 residual diagnostics.
The exported adapter is not claimed to be unmodified upstream training code.

## Wildfire-Aware Search And Audits

The modified loading-dependent exposure term sums environmental score times
squared apparent loading over every energized transmission risk line. It is
normalized by the stored Scenario-16 baseline, not a new intact economic optimum.
The environmental score is not a calibrated ignition probability. This extends
the risk representation of the original OPS formulation, not its exact reproduction.

Texas Phase I uses lambda 0.8, K0 + 50 K1 + up to 250 K2, five ranked K1 parents,
the original eligibility/tie/deduplication rules, and at most twenty actual alpha
objective calls per topology. Native-to-AC differences can arise because surrogate
state generation is not a wildfire-aware economic optimization.

Reference A fixes topology and service and solves economic AC-OPF. B1 maximizes
service at fixed topology. B2 economically resolves B1's delivered service. A
legitimate B2 failure preserves B1 service/diagnostics with economic cost unavailable;
B1 failure cannot certify service. Local numerical solves are not global proofs.

## Reporting

Empirical frontiers, best-so-far topology curves and rank/overlap definitions are
exported directly from Stage L in `reporting_metrics.py`. Spearman can be undefined
under the retained all-shared-K1 definition; it is not silently replaced by zero.
Phase I's empirical frontier is only within the evaluated lambda-0.8 pool.
Architecture-specific raw losses are not a cross-model electrical metric.
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
