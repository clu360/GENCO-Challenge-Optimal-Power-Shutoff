# Stage M Phase I Results: Verified Complete

Phase I is scientifically complete. The original PHASE_I_RESULTS_COMPLETE gate
passed on reporting job 14465507. Eight fits/validations, six full searches and
six designated AC audits are accepted. Phase II remains held. See
[closure verification](PHASE_I_COMPLETION.md). Earlier dated observations are history.

Certified training fits: 8/8. Training completion does not certify downstream validation, OPS or exact AC references.

## Exact Audited Decisions

| model | topology_key | native_r | shed | a_r | a_j | a_cost | maximum_service_fraction | b_r | b_cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GENCO G100 -> R400 | 117;281 | 1.45001 | 0.000486234 | 1.08904 | 0.871331 | 326415 | 1 | 1.09629 | 318552 |
| GENCO G100 -> W400 | 117;281 | 1.51118 | 0.000546406 | 1.08906 | 0.871357 | 326325 | 1 | 1.09629 | 318552 |
| GENCO G500 | 117;1548 | 1.27011 | 0.00269693 | 1.16414 | 0.931855 | 296511 | 1 | 1.17187 | 296967 |
| OpenGridSFM G100 -> R400 | 45;766 | 1.10303 | 0 | 1.08426 | 0.867408 | 302088 | 1 | 1.10015 | 295177 |
| OpenGridSFM G100 -> W400 | 281;850 | 1.00753 | 0.000112819 | 1.0882 | 0.870581 | 330999 | 1 | 1.09288 | 323571 |
| OpenGridSFM G500 | 3272;3273 | 1.09574 | 0.000328131 | 1.08228 | 0.865891 | 309036 | 1 | 1.09224 | 304244 |

Reference A is economic AC-OPF at the selected topology and fixed load-service commands, not wildfire-aware reoptimization. B1 certifies maximum fixed-topology service; B2 minimizes economic cost at that service. Local solves do not prove global optimality.

All available GENCO A risks exceed the stored baseline of1. Sequential R/W select the same two physical lines, while G500 selects a different second line. These exact decisions do not establish a below-baseline wildfire benefit. Native eligibility and lower training loss are not physical-feasibility certificates.

## OpenGridSFM Audited Outcomes

| model | topology_key | native_r | a_r | delta_r_a | shed | a_j | native_overloaded_lines |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenGridSFM G100 -> R400 | 45;766 | 1.10303 | 1.08426 | -0.0187724 | 0 | 0.867408 | 10 |
| OpenGridSFM G100 -> W400 | 281;850 | 1.00753 | 1.0882 | 0.0806665 | 0.000112819 | 0.870581 | 2 |
| OpenGridSFM G500 | 3272;3273 | 1.09574 | 1.08228 | -0.0134623 | 0.000328131 | 0.865891 | 5 |

The native model selects its own K2 trajectory, not the GENCO trajectory. Risk discrepancies can have either sign; smaller predicted risk is not necessarily smaller AC-recovered risk. Every published native AC-A risk remains above the authoritative stored baseline of1. B1 recovers essentially full service within solver tolerance; B2 economic states and risk diagnostics are distinct from the fixed-service economic A states. This is one exploratory scenario and one lambda, not evidence of general model superiority.

The report reproduces Stage L empirical-frontier, incumbent, rank-correlation/Jaccard, geographic projection and AC-minus-native discrepancy conventions. Only lambda0.8 was searched: no multi-lambda, global Pareto, broad-generalization or statistical-superiority claim is made.

Validation histories and per-record metrics are development evidence. Native model-specific losses and selection scores are not cross-family common metrics. G/R/W histories use their assigned validation distributions. Canonical AC label acceptance and FP32 representation diagnostics remain distinct.

## Computation

| model | topologies | eligible | recorded_evaluator_seconds | median_topology_seconds | median_call_seconds |
| --- | --- | --- | --- | --- | --- |
| GENCO G100 -> R400 | 301 | 289 | 3162.57 | 10.6769 | 0.533843 |
| GENCO G100 -> W400 | 301 | 289 | 3392.02 | 11.4516 | 0.572582 |
| GENCO G500 | 301 | 289 | 3271.22 | 11.0244 | 0.551222 |
| OpenGridSFM G100 -> R400 | 301 | 301 | 1998.97 | 6.63773 | 0.331886 |
| OpenGridSFM G100 -> W400 | 301 | 301 | 2737.63 | 9.09398 | 0.454699 |
| OpenGridSFM G500 | 301 | 301 | 1982.86 | 6.58945 | 0.329472 |

Timing is logical recorded evaluator time, not queue time or a controlled architecture-only speed comparison. Inferno billing is not inferred from these numbers.

## Fine-Tuning And Validation

| task_id | current_fit_examples | total_unique_examples | selected_epoch | optimizer_steps | gpu | recorded_wall_seconds | wall_scope |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v070.genco_opf.G100.s0 | 100 | 100 | 18 | 2000 | NVIDIA H200 | 886.903 | CURRENT_ATTEMPT_ONLY |
| v070.genco_opf.G100_to_R400.s0 | 400 | 500 | 16 | 8000 | NVIDIA A100-SXM4-80GB | 2764.1 | CURRENT_ATTEMPT_ONLY |
| v070.genco_opf.G100_to_W400.s0 | 400 | 500 | 18 | 8000 | NVIDIA H100 80GB HBM3 | 2947.19 | CURRENT_ATTEMPT_ONLY |
| v070.genco_opf.G500.s0 | 500 | 500 | 18 | 10000 | NVIDIA A100-SXM4-80GB | 3662 | CURRENT_ATTEMPT_ONLY |
| v070.opengridsfm.G100.s0 | 100 | 100 | 4 | 2000 | NVIDIA H200 | 1138.55 | CURRENT_PROCESS_ONLY_NOT_TOTAL_RESUME_WALL |
| v070.opengridsfm.G100_to_R400.s0 | 400 | 500 | 19 | 8000 | NVIDIA H200 | 2872.98 | CURRENT_PROCESS_ONLY_NOT_TOTAL_RESUME_WALL |
| v070.opengridsfm.G100_to_W400.s0 | 400 | 500 | 19 | 8000 | NVIDIA H200 | 2367.5 | CURRENT_PROCESS_ONLY_NOT_TOTAL_RESUME_WALL |
| v070.opengridsfm.G500.s0 | 500 | 500 | 19 | 10000 | NVIDIA H100 80GB HBM3 | 0.971361 | CURRENT_PROCESS_ONLY_NOT_TOTAL_RESUME_WALL |

G100 is the intermediate lineage checkpoint, not a fourth final OPS representative. Each sequential final has100 Grid plus400 task examples; the task-stage optimizer counter does not include the G100 parent updates. The accepted master pools contain500 G,400 R and400 W training examples and100 validation examples per distribution. Membership is not inferred from optimizer-step counts. Resume/current-attempt wall times are not falsely presented as whole-run totals.

| checkpoint_task | distribution | records | vm_rmse_pu | mean_max_abs_p_residual_mw | mean_max_loading |
| --- | --- | --- | --- | --- | --- |
| v070.genco_opf.G100.s0.validation | G | 100 | 0.0705417 | 4576.61 | 9.5128 |
| v070.genco_opf.G100.s0.validation | O | 100 | 0.0696842 | 4653.63 | 9.51279 |
| v070.genco_opf.G100.s0.validation | R | 100 | 0.0703644 | 4660.76 | 9.81508 |
| v070.genco_opf.G100_to_R400.s0.validation | G | 100 | 0.0721734 | 9311.85 | 4.67716 |
| v070.genco_opf.G100_to_R400.s0.validation | O | 100 | 0.0712851 | 9011.44 | 4.68649 |
| v070.genco_opf.G100_to_R400.s0.validation | R | 100 | 0.0720065 | 9300.28 | 4.88778 |
| v070.genco_opf.G100_to_W400.s0.validation | G | 100 | 0.0702344 | 9841.29 | 4.92592 |
| v070.genco_opf.G100_to_W400.s0.validation | O | 100 | 0.0693357 | 9594.05 | 4.92558 |
| v070.genco_opf.G100_to_W400.s0.validation | R | 100 | 0.0700746 | 9846.76 | 4.96591 |
| v070.genco_opf.G500.s0.validation | G | 100 | 0.0805942 | 6264.76 | 4.24752 |
| v070.genco_opf.G500.s0.validation | O | 100 | 0.0796398 | 6600.09 | 4.31989 |
| v070.genco_opf.G500.s0.validation | R | 100 | 0.080422 | 6559.56 | 5.12753 |
| v070.opengridsfm.G100.s0.validation | G | 100 | 0.030083 | 19721.1 | 18.0101 |
| v070.opengridsfm.G100.s0.validation | O | 100 | 0.0318493 | 19137.6 | 18.5421 |
| v070.opengridsfm.G100.s0.validation | R | 100 | 0.0302697 | 20633.6 | 18.6815 |
| v070.opengridsfm.G100_to_R400.s0.validation | G | 100 | 0.0403625 | 601.7 | 1.03714 |
| v070.opengridsfm.G100_to_R400.s0.validation | O | 100 | 0.0422018 | 956.432 | 1.26847 |
| v070.opengridsfm.G100_to_R400.s0.validation | R | 100 | 0.040645 | 740.775 | 1.2389 |
| v070.opengridsfm.G100_to_W400.s0.validation | G | 100 | 0.0403625 | 690.118 | 1.00225 |
| v070.opengridsfm.G100_to_W400.s0.validation | O | 100 | 0.0422018 | 721.044 | 1.04326 |
| v070.opengridsfm.G100_to_W400.s0.validation | R | 100 | 0.040645 | 843.165 | 1.16777 |
| v070.opengridsfm.G500.s0.validation | G | 100 | 0.0403625 | 515.027 | 0.991397 |
| v070.opengridsfm.G500.s0.validation | O | 100 | 0.0422018 | 1307.1 | 1.73112 |
| v070.opengridsfm.G500.s0.validation | R | 100 | 0.040645 | 1070.44 | 1.69322 |

The validation table compares physical diagnostics on shared distribution assignments; raw GENCO and native losses/selection scores are architecture-specific. Training PASS is not operational feasibility. GENCO sequential adaptation improves some voltage diagnostics but can worsen balance residuals relative to G500; inspect the retained per-record distributions rather than treating one scalar loss as sufficient. No released-base validation is fabricated where it was not evaluated on this saved split.

## Coverage And Evidence

| task_id | executor | status | job_id |
| --- | --- | --- | --- |
| v070.genco_opf.G100.s0 | genco_fit | PASS | None |
| v070.genco_opf.G100.s0.validation | genco_evaluation | PASS | None |
| v070.genco_opf.G100_to_R400.s0 | genco_fit | PASS | None |
| v070.genco_opf.G100_to_R400.s0.phase_i.ops | ops_trajectory | PASS | None |
| v070.genco_opf.G100_to_R400.s0.phase_i.refs | ops_references | PASS | None |
| v070.genco_opf.G100_to_R400.s0.validation | genco_evaluation | PASS | None |
| v070.genco_opf.G100_to_W400.s0 | genco_fit | PASS | None |
| v070.genco_opf.G100_to_W400.s0.phase_i.ops | ops_trajectory | PASS | None |
| v070.genco_opf.G100_to_W400.s0.phase_i.refs | ops_references | PASS | None |
| v070.genco_opf.G100_to_W400.s0.validation | genco_evaluation | PASS | None |
| v070.genco_opf.G500.s0 | genco_fit | PASS | None |
| v070.genco_opf.G500.s0.phase_i.ops | ops_trajectory | PASS | None |
| v070.genco_opf.G500.s0.phase_i.refs | ops_references | PASS | None |
| v070.genco_opf.G500.s0.validation | genco_evaluation | PASS | None |
| v070.opengridsfm.G100.s0 | native_fit | PASS | None |
| v070.opengridsfm.G100.s0.validation | native_evaluation | PASS | 14404784 |
| v070.opengridsfm.G100_to_R400.s0 | native_fit | PASS | None |
| v070.opengridsfm.G100_to_R400.s0.phase_i.ops | ops_trajectory | PASS | 14406004 |
| v070.opengridsfm.G100_to_R400.s0.phase_i.refs | ops_references | PASS | 14430963 |
| v070.opengridsfm.G100_to_R400.s0.validation | native_evaluation | PASS | 14404786 |
| v070.opengridsfm.G100_to_W400.s0 | native_fit | PASS | None |
| v070.opengridsfm.G100_to_W400.s0.phase_i.ops | ops_trajectory | PASS | 14407728 |
| v070.opengridsfm.G100_to_W400.s0.phase_i.refs | ops_references | PASS | 14441412 |
| v070.opengridsfm.G100_to_W400.s0.validation | native_evaluation | PASS | 14406007 |
| v070.opengridsfm.G500.s0 | native_fit | PASS | 14403492 |
| v070.opengridsfm.G500.s0.phase_i.ops | ops_trajectory | PASS | 14423205 |
| v070.opengridsfm.G500.s0.phase_i.refs | ops_references | PASS | 14442714 |
| v070.opengridsfm.G500.s0.validation | native_evaluation | PASS | 14419514 |

Full request/artifact hashes, failure evidence and resume state remain in protected private archives. The standalone release must sanitize personal/cluster paths separately; this research inventory preserves original evidence without rewriting receipts. Pending native OPS/reference outcomes are not zeros or extrapolations.

The original Stage L all-shared-K1 Spearman statistic is undefined when ineligible candidates have nonfinite merits; the table preserves this as null/NaN rather than zero. Parent/finalist/K2 Jaccard remains defined. No hidden finite-only filtering or favorable correlation is substituted.
