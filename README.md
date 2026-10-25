# GENCO Challenge: Optimal Power Shutoff

Research on budgeted wildfire-aware topology decisions using neural grid-state
evaluators and exact AC audits. GOC-500 and modified Texas2k are separate studies,
not pooled error benchmarks.

**Release preparation in progress.** Completed GENCO results and certified native
models are available in this local package. Independent OPS/demo and final Git
release checks are not yet certified. This is not a challenge-form submission.

## Completed Findings

Texas2k Phase I uses Scenario16, the frozen June23,2023 4PM CDT cumulative-hazard
snapshot, lambda_R0.8, and the original alpha-only hierarchical search. Each
completed GENCO variant evaluated301 topology states and6020 objective calls.
Economic AC Reference A risks are1.164144 for G500,1.089042 for G100-to-R400,
and1.089060 for G100-to-W400. All exceed the stored baseline of1. The sequential
variants select physical lines117/281; G500 selects117/1548. Reference B recovers
essentially full service under the solver tolerance. These are local audit
outcomes, not global optimality or broad generalization claims.

| Study | Models | Published evidence | Current limitations |
|---|---|---|---|
| GOC-500 | Released GridSFM; FT0 smoke; M1; sibling M2/M3 adaptations | Retained Stage J physical evaluations and FT3/FT4 OPS tables | Official sample demo is not the historical test population |
| Texas2k K/L | Historical DC/AC/GridSFM and three released GENCO branches | Recorded historical tables, separately labeled | Different evaluator/search/control policies; PF redispatch exploration was limited |
| Texas2k M | GENCO-OPF G500/G100-to-R400/G100-to-W400; certified native models | Three complete GENCO searches and exact A/B audits; available validation | Native G500 certification and native OPS/AC pending; Phase II held |

Read [the Phase I report](experiments/texas2k/results/stage_m/reports/PHASE_I_RESULTS.md)
and [methodology](experiments/texas2k/results/stage_m/reports/METHODOLOGY.md).
Model/data channels and completion states are machine-readable in
`artifacts/model_catalog.json`. Large weights are delivered through a checksum-bound
model bundle, not ordinary Git objects. Remote publication is not yet claimed.

## Results-Only Use

```sh
python -m pip install -e '.[notebooks,test]'
genco-ops results --study texas2k --output outputs/texas2k
genco-ops results --study goc_500 --output outputs/goc500
```

These commands regenerate numerical summaries and main figures from included
tables without model downloads, GPU, Julia, solver licenses or cluster access.
Execution/verification receipts will identify the commands actually tested.

## Model Inference

Use the separately pinned `environments/model_cpu_requirements.txt` in an isolated
Python environment. PyTorch CPU wheels are installed from the official CPU index;
the matching PyG scatter wheel and exact upstream Git commits are pinned. GridSFM's
official package lives in the upstream `model/` subdirectory.

Acquire the explicitly supplied model bundle with `genco-ops acquire --bundle
model_weights.zip`. Select an actual ID from `artifacts/model_catalog.json`, then
run `genco-ops infer --model goc500.m1 --output outputs/model_demo`.
Finite inference is not AC feasibility. Native and GENCO raw validation losses
are not comparable across architectures.

Texas2k raw graph inputs are kept private pending source/redistribution review.
The exact unavailable mode is fresh public Texas2k inference/full computation
without separately authorized inputs. Model weights and saved result exploration
are separate from that restriction. No unavailable case is replaced by a different
grid and called the same reproduction.

## Reproduction Scope

The notebooks are explicit, bounded entry points. They never launch training,
cluster jobs or paid computation on opening. Published-result exploration, new
demo predictions, and full original OPS/reference reproduction are distinct.
Original full configurations and executable OPS/AC handoffs remain to be release-
qualified; the current finite-inference checks are not a full campaign rerun.

The scientific archive preserves failed solves, exact states, immutable request
identities and full resume state. Public text locators are sanitized; numeric
table values and physical line identities are unchanged. Personal cluster paths,
accounts, credentials and raw private archives are not part of this repository.
