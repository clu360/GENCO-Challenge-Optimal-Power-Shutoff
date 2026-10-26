# Reproduction workflows

Run from the repository root using Python 3.12 in a short, writable checkout.
[Installation](installation.md) separates the results environment from the pinned
CPU model environment. [Artifact acquisition](artifacts.md) explains the models
and data each workflow requires.

## Inspect the published experiments

```sh
python -m pip install -e '.[notebooks,test]'
genco-ops results --study goc_500 --output outputs/goc500_results
genco-ops results --study texas2k --output outputs/texas2k_results
python scripts/execute_notebooks.py
```

These commands read included numeric evidence and regenerate figures. They do
not train models, predict new states, launch topology searches or solve AC-OPF.
GOC FT3/FT4, FT6, refined FT7 and RQ1 evidence retain distinct provenance;
Texas K/L historical comparisons remain separate from Stage M Phase I.

| Notebook | Scope |
|---|---|
| `01_explore_published_results.ipynb` | Rebuild and explain both studies' published findings |
| `02_goc500_model_and_ops_demo.ipynb` | Select GOC checkpoints; run official-sample inference and a bounded new OPS demo |
| `03_texas2k_model_and_ops_demo.ipynb` | Select Texas checkpoints; inspect evidence and execute paths with exact authorized inputs |
| `04_public_genco_ieee14.ipynb` | Run real GENCO inference on public GraphKit inputs |

New execution products go under `outputs/`. Select a notebook and require actual
numerical execution with:

```sh
python scripts/execute_notebooks.py --notebook 02_goc500_model_and_ops_demo.ipynb --require-model-execution
```

`--models` selects all four notebooks; `--in-place` explicitly saves measured
outputs into the source notebooks. Missing inputs remain unavailable. Notebook
completion with unavailable modes is not a passed inference check.

The current [execution receipt](../artifacts/reproduction_verification.json)
records all fifteen checkpoint loads and the actual notebook outcomes: GOC
M0-M3 sample predictions, the 16-call GOC demo and the public GENCO prediction
passed; exact Texas saved-case/probe inputs remain unavailable in the independent
checkout. Executed source notebooks preserve both the outputs and these limits.

## Choose a checkpoint and run the supported model path

The repository and model archives are public; the
[public-access receipt](../artifacts/public_release_verification.json) records
signed-out access. Exact modified Texas electrical inputs remain private.

In the [CPU model environment](installation.md):

```sh
python scripts/download_models.py
genco-ops models --study goc_500 --verify-hashes
genco-ops models --study texas2k --json
```

Selectors report model/input presence separately from verified hashes. Numerical
paths check the required model and input identities before deserializing them.
Model lineage is in `artifacts/model_catalog.json`.

The shared `run` command prints a plan unless `--execute` is present:

```sh
genco-ops run --study goc_500 --model goc500.m2 --mode infer --output outputs/m2_inference
genco-ops run --study goc_500 --model goc500.m2 --mode infer --output outputs/m2_inference --execute
genco-ops run --study goc_500 --model goc500.m2 --mode demo --output outputs/m2_ops_demo --execute
```

Inference predicts one pinned official sample. The demo uses that same electrical
sample with synthetic uniform hazard, two topologies and its own small continuous
budget. It records a distinct study identity; it is not the historical
three-scenario search or 750-case validation population. `infer` and `ops-demo`
remain available as direct entry points.

### Public GENCO compatibility example

Notebook 04 or this command runs actual GENCO-OPF inference with the released
checkpoint/normalizer and original masked OPF transforms:

```sh
genco-ops public-genco --output outputs/public_ieee14 --scenario 0 --execute
```

Omit `--execute` to inspect the plan. The ten public raw Parquet fixtures are
pinned to the official GraphKit commit with Git-blob parity and SHA-256
provenance. Processing and decoded predictions go into a fresh output directory.
IEEE14 supplies a public interface demonstration: it does not measure
Texas accuracy, fine-tuning benefit, AC feasibility or OPS quality. See its
[input documentation](../experiments/ieee14_public/README.md).

## Texas numerical reproduction with authorized electrical inputs

The exact modified grid is private; public weather coefficients alone cannot
reconstruct it. An inference pack supplies the catalogued graph bytes:

```sh
genco-ops run --study texas2k --model texas2k.genco_opf.G500 --mode infer --inputs /authorized/graphpack --output outputs/genco_prediction --execute
```

`--inputs` accepts an exact saved graph, a directory of named graph fixtures, or
a directory mirroring the catalog tree. The catalog SHA remains mandatory.

The original OPS executor uses a different contract: eight prepared Parquet
tables plus `input_contract.json`. A single-topology CPU probe runs the original
20-call continuous optimizer with a separate output identity:

```sh
genco-ops run --study texas2k --model texas2k.genco_opf.G500 --mode published --inputs /authorized/prepared --device cpu --probe-topology '117;281' --output outputs/genco_probe --execute
```

Use `intact` or sorted line IDs separated by semicolons for `--probe-topology`.
The full frozen Phase I search requires one qualified CUDA GPU:

```sh
genco-ops run --study texas2k --model texas2k.genco_opf.G500 --mode published --inputs /authorized/prepared --device cuda:0 --output outputs/genco_full
genco-ops run --study texas2k --model texas2k.genco_opf.G500 --mode published --inputs /authorized/prepared --device cuda:0 --output outputs/genco_full --execute
```

The plan validates the supplied input pack. Explicit execution preserves the
original 301-state/6,020-call ceiling, hierarchical K0/K1/K2 search, five selected
load controls, resident evaluator and durable journal. Checkpoint, runtime and
device changes cannot silently resume another trajectory. Intermediate/base
checkpoints are not final Phase I representatives. No command submits Slurm jobs
or starts training. The direct `phase-i-ops` entry point remains.

The exported original source has prior CPU portability/parity evidence. Full
CUDA transport and a complete 301-state run have not been independently rerun
for this packaging update. A new probe is not a historical full-search replay.

## Recover the historical GOC FT6 evaluation inputs

The official source objects and all 750 ordered graph fingerprints have been
identified: 375 FullTop and 375 N-1 cases. The default command only shows a plan:

```sh
python scripts/recover_goc500_evaluation_data.py
```

Explicit recovery transfers approximately 2.4 GB before decompression:

```sh
python -m pip install -e '.[recovery]'
python scripts/recover_goc500_evaluation_data.py --download
python scripts/recover_goc500_evaluation_data.py --prepare
```

The utility pins GCS object generation, byte counts and CRC32C, then matches each
selected graph's tensor SHA and restores the historical order. Preparation writes
two 375-graph dictionary files and a receipt; it performs no model evaluation or
AC solve. Full archive recovery and the historical 750-case metric replay have
**not** been performed in this release. The original evaluation used PyG
2.8.0.post1, distinct from the portable one-case environment. Read the
[data recipe](../experiments/goc_500/data/README.md) before replaying it.

Recovering FT6 inputs does not recover the separate historical OPS baseline,
PAC-freeze inputs or legacy execution state. Frozen candidate pools and recorded
OPS outcomes remain included; the sample demo does not substitute for them.

## Optional exact AC audit

The real Julia adapter accepts an authorized MATPOWER case and a fixed-decision
JSON; it prepares commands by default:

```sh
julia --project=environments/julia -e 'using Pkg; Pkg.instantiate()'
python scripts/ac_audit.py --decision decision.json --case authorized_case.m --output outputs/audit
```

Add `--execute` deliberately to solve. The JSON schema is
`OPF_FIXED_TOPOLOGY_SERVICE_A_AND_MAX_SERVICE_B_V1`: case SHA, zero-based
`offline_branch_ids`/`sourceless_load_ids`, complete `alpha` and `p_env`
dictionaries keyed by physical IDs, `r_base`, `lambda_r`, and the Reference B
service tolerance. The original Julia source, Project and Manifest are included.

Reference A fixes topology/service and minimizes economic generation cost.
Reference B maximizes AC-feasible service, then economically dispatches at that
service level. Neither is the proposed risk-constrained shortlist refinement.
Command and identity mapping have bounded checks; independent numerical Julia
execution remains unqualified. Inspect physical acceptance diagnostics before
certifying a newly solved point. Existing accepted A/B tables can be explored
without installing Julia.
