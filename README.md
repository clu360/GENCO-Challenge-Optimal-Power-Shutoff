# GENCO Challenge: Optimal Power Shutoff

Research on budgeted wildfire-aware topology decisions using neural grid-state
evaluators and exact AC audits. GOC-500 and modified Texas2k are separate studies,
not pooled error benchmarks.

**Completed-results export with bounded numerical demos.** Completed GENCO results
and certified native models are included through a checksum-bound local export.
See `docs/RELEASE_VERIFICATION.md` for clean-checkout evidence and explicit
unsupported modes. This is not a challenge-form submission or full Phase I closure.

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
| Texas2k M | GENCO-OPF G500/G100-to-R400/G100-to-W400; all eight training fits certified | Three complete GENCO searches and exact A/B audits; available validation | Native OPS/AC pending; Phase II held |

Read [the Phase I report](experiments/texas2k/results/stage_m/reports/PHASE_I_RESULTS.md)
and [methodology](experiments/texas2k/results/stage_m/reports/METHODOLOGY.md).
Model/data channels and completion states are machine-readable in
`artifacts/model_catalog.json`. Large weights are delivered through a checksum-bound
model archives, not ordinary Git objects. The verified
[private source/model release](https://github.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/releases/tag/phase-i-models-v152)
requires repository access. Its visibility has not been changed to public.

## Results-Only Use

```sh
python -m pip install -e '.[notebooks,test]'
genco-ops results --study texas2k --output outputs/texas2k
genco-ops results --study goc_500 --output outputs/goc500
```

These commands regenerate numerical summaries and main figures from included
tables without model downloads, GPU, Julia, solver licenses or cluster access.
Execution/verification receipts identify the commands actually tested.

## Model Inference

Use the separately pinned `environments/model_cpu_requirements.txt` in an isolated
Python environment. PyTorch CPU wheels are installed from the official CPU index;
the matching PyG scatter wheel and exact upstream Git commits are pinned. GridSFM's
official package lives in the upstream `model/` subdirectory.

Acquire the primary model bundle and the G500 supplement using the two explicit
commands in `docs/reproduction.md`. Each has its own immutable checksum; previous
model exports remain unchanged. Select an actual ID from `artifacts/model_catalog.json`, then
run `genco-ops infer --model goc500.m1 --output outputs/model_demo`.
Run `genco-ops ops-demo --model goc500.m1 --output outputs/new_ops_demo`
for a real bounded CPU search on the official sample: two topologies and eight
actual calls each, under an explicitly synthetic uniform hazard. It is not the
published full search. Finite inference is not AC feasibility. Native and GENCO raw validation losses
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
The optional fixed-decision AC adapter exports the unchanged Julia formulation;
its command mapping is tested but independent numerical Julia execution is not.
The original Texas numerical executor is now exported with exact source bindings
and tested20-call GENCO/native probes. Its full CUDA run was not repeated, and
public input rights remain unresolved. Historical GOC full-population execution
is separate and not substituted by the sample demo. These omissions are not
represented as successful full recomputation. See [reproduction](docs/reproduction.md) and
[limitations](docs/results_and_limitations.md).

The scientific archive preserves failed solves, exact states, immutable request
identities and full resume state. Public text locators are sanitized; numeric
table values and physical line identities are unchanged. Personal cluster paths,
accounts, credentials and raw private archives are not part of this repository.
