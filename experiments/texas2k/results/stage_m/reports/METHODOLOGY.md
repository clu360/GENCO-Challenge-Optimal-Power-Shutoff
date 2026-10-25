# Implemented Methodology And Stage L Reporting Reuse

| Figure family | Actual Stage L implementation reused | Stage M structured evidence | Adaptation |
|---|---|---|---|
| Empirical tradeoff | post_run_analysis.py native Pareto block; shared reporting_metrics.empirical_frontier | candidate_results, finalists, exact references | One lambda0.8; model adaptation labels; shared scales; audited markers only |
| Outer convergence | post_run_analysis.py incumbent block; shared topology_incumbent | candidate_results | Model-specific attempt order; merit, not exact AC convergence |
| Inner trial profiles | post_run_analysis.py continuous_budget_summary | continuous_evaluations | Median per call index; not a monotone convergence certificate |
| Divergence | post_run_analysis.py K1 ranking block; shared rank_divergence | k1_parents, k2_provenance, finalists | Preserve legacy undefined correlations; add labeled K2 overlap |
| Geographic maps | post_run_analysis.py LineCollection/longitude-latitude equal-aspect projection | canonical_branch, proxy_components, finalists | One map per completed checkpoint, physical IDs and common hazard input |
| Economic A discrepancy | post_run_analysis.py AC-minus-native deltas | reference_a2 and finalist states | Bars at lambda0.8, not lines implying a lambda sweep |
| B service/economics | post_run_analysis.py B1/B2 comparison | reference_b and retained solver states | Preserve B1/B2 eligibility/fallback; never impute cost |
| Historical context | post_run_analysis.py Stage K/L comparison | retained K/L tables, input fingerprints, Stage M exact results | Match lambda0.8; explicitly partial comparability |
| Fine-tuning diagnostics | Existing Stage M native/GraphKit histories and physical evaluators | fit metadata, validation metrics | Separate native losses, physics components, selection scores and common physical quantities |

## Frozen Numerical Contract

Phase I is an exploratory modifiedTexas2k Scenario16 case with the exact June23,
2023 4PM CDT cumulative-hazard snapshot. The raw electrical case, loading history,
geography and environmental hashes are retained in prepared/input_manifest.json.
R_base is the authoritative stored-loading value, not recomputed from a new
intact AC optimum. Exposure is cumulative environmental score times squared
physical apparent loading, summed over every energized Ltrans branch and
normalized by R_base. This is a loading-dependent exposure proxy, not a calibrated
ignition probability or an unchanged reproduction of the original OPS risk model.

Each final checkpoint uses intact plus50 shared K1 candidates, then up250 distinct
K2 candidates generated from its own five eligible best K1 parents. Preserve
canonical zero-based physical line IDs, sorted outage pairs, proxy costs, tie
handling and deduplication. Both Phase I families use five topology-relative
alpha controls and the separately versioned alpha-only20-actual-call Powell
executor. There is no PF redispatch fine-tuning or r optimization in Phase I.
Native tradeoff merit is lambda_R*R_norm+(1-lambda_R)*shed at lambda_R0.8;
operational/physics diagnostics and penalties remain separately recorded under
the actual frozen evaluator contracts, not silently added to exact-reference J.

Training uses economic AC-OPF ground-truth labels and accepted paired G/R/W
operating conditions. The approved bounded replacement/connected-sampling
amendments preserve matched sets, splits and failure evidence; convergence-
conditioned sampling limits generalization. W is wildfire-ranked topology
sampling, not AC-OPS-optimal continuous decisions or a discovery-bank sweep.
Grouped train/validation independence and normalization are fixed by accepted
requests; no validation or OPS outcome chooses replacement samples.

GENCO-OPF uses its pinned GraphKit architecture/source and released normalization.
OpenGridSFM uses the native package at its pinned commit, with the approved
stage_m_exact_impedance_fp64_kcl_v015 adapter and canonical-AC target acceptance
with mandatory FP32 diagnostics. Its FP32 model is not described as an unmodified
native physics loss. Neither model selects checkpoints using OPS/AC audit results.

Reference A fixes selected topology/service and economically reoptimizes AC
dispatch, unlike the wildfire-aware candidate objective. B1 maximizes AC service
at fixed topology; B2 resolves economic cost at certified B1 service. A legitimate
B2 failure preserves B1 diagnostics/service with unset economic cost. A B1 failure
does not certify maximum service. Solver outcomes are local, not global proofs.

The independently grouped unseen-topology and confirmatory scenarios are not
replaced by Phase I validation. They are not newly run here. Phase II is held.
Historical Stage L PF r=0 exploration limitations remain historical, not a claim
about the current OPF adaptation experiment. See HISTORICAL_COMPARABILITY.json
before interpreting any K/L/M delta as a controlled improvement or speedup.
