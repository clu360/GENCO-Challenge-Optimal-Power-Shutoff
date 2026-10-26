# Reproduction

## Results Without Models Or Solvers

Install `pip install -e '.[notebooks,test]'` in Python 3.12, then run:
Use a short writable checkout path on Windows; the independent tests used an
isolated temporary checkout, not deeply nested development directories.

```sh
genco-ops results --study texas2k --output outputs/texas2k
genco-ops results --study goc_500 --output outputs/goc500
python -m pytest tests -q
```

The first notebook reads both studies without training, network access or model
downloads. Full candidate/objective traces are retained as Parquet; compact CSVs
are convenience views, not replacement evidence. No raw model loss is relabeled
as a common physical error.

## Real Model Inference

Use a separate environment with the pinned `environments/model_cpu_requirements.txt`.
Install torch 2.8.0 CPU from the official CPU index before the remaining packages.
The GraphKit and Microsoft source commits are fixed in that manifest. Obtain the
supplied local model export and run:

```sh
genco-ops acquire --bundle /path/to/genco_challenge_models_v149.zip
genco-ops acquire --bundle /path/to/opengridsfm_G500_v152.zip
genco-ops infer --model goc500.m1 --output outputs/goc500_inference
genco-ops ops-demo --model goc500.m1 --output outputs/new_goc500_ops
```

The primary bundle, G500 supplement and every member checksum are in
`artifacts/model_bundle.json`. The supplement adds the newly certified native
G500 checkpoint and its MIT notice without repacking or replacing earlier weights.
Both archives together provide all current catalog entries; acquisition is explicit,
local and idempotent. Native G500 validation/OPS/AC work is separate from fit certification.
Both archives are also available from the verified
[private GitHub release](https://github.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/releases/tag/phase-i-models-v152).
Sign into an authorized GitHub account to download them, then run the same explicit
local acquisition commands above. Both complete authenticated downloads were
SHA-256 checked in a clean remote clone, acquired there, and all fifteen catalog
entries genuinely loaded. See `artifacts/hosted_release_verification.json`.
The original local export remains an independently verified alternative.
Texas input graphs are not publicly distributed until redistribution rights are
resolved. The Texas notebook marks an absent authorized input as UNAVAILABLE,
not PASS. No paid compute, cluster login or hidden research import is required
for the supported GOC sample inference path.

## Exact AC Adapter

`scripts/ac_audit.py` accepts an authorized electrical case and an explicit
fixed-decision JSON. The schema is `OPF_FIXED_TOPOLOGY_SERVICE_A_AND_MAX_SERVICE_B_V1`:
`case_sha256`, zero-based `offline_branch_ids`/`sourceless_load_ids`, complete `alpha`
and `p_env` dictionaries keyed by zero-based physical identities, stored `r_base`,
`lambda_r`, and `reference_b_service_tolerance_mw`. The unchanged Julia source,
Project and Manifest are exported under `environments/julia/`.

```sh
julia --project=environments/julia -e 'using Pkg; Pkg.instantiate()'
python scripts/ac_audit.py --decision decision.json --case authorized_case.m --output outputs/audit
```

Preparation writes the exact A/B commands and controls without solving. Add
`--execute` only deliberately. No topology search or scientific decision is
silently changed. Numerical AC execution in the independent release is **untested**;
command/identity mapping has bounded regression coverage. Solver eligibility alone
does not certify physical quality. Use original numerical acceptance checks on
the retained bus/generator/branch tables before reporting a certified new outcome.
Existing accepted AC audit results remain available without Julia.

## Original Texas Numerical Executor

`experiments/texas2k/configs/phase_i_original.json` exports the actual recipe and
search settings, with explicit source/request identities. Loading it does not run
anything. The original resident evaluators, graph preprocessing, physical metrics,
alpha-only optimizer, durable objective journal and hierarchical outer search are
exported in `src/genco_ops/published/`. The source manifest identifies66 exported
definitions across22 original modules, with only recorded import/I/O redirections.
The constructor receives the same generator-cost table explicitly; it does not
look for private files through the old research package.

With a separately authorized exact input pack and acquired checkpoints:

```sh
genco-ops phase-i-ops --model texas2k.genco_opf.G500 --inputs /authorized/inputs --output outputs/full_g500
genco-ops phase-i-ops --model texas2k.genco_opf.G500 --inputs /authorized/inputs --output outputs/full_g500 --device cuda:0 --execute
```

The first command validates an input/configuration plan without inference. The
second explicitly starts the original full search; it must not be run as a casual
release test. One visible qualified CUDA GPU is required. Full CUDA transport and
the full301-state computation were **not** rerun during independent packaging;
no untested GPU/platform support or full-recomputation claim is made.

A bounded CPU probe uses the original risk/scoring and20-call search on one
explicit K0/K1/K2 topology, with a separate output identity:

```sh
genco-ops phase-i-ops --model texas2k.genco_opf.G500 --inputs /authorized/inputs --output outputs/new_probe --device cpu --probe-topology '117;281' --execute
python scripts/check_texas_contract.py --inputs /authorized/inputs --output outputs/source_contract.json
```

Both GENCO and native20-call probes were actually tested on authorized inputs.
Twelve normalized input tensors match the retained Stage L S1 fixture bitwise;
its physical bus/generator/branch tables match exactly. Prediction drift from
the older recorded runtime is diagnostic, not claimed bitwise parity or a relaxed
AC-label gate. Existing accepted proxy files are byte-verified and reused, not
silently recomputed under a different platform's scalar `pow` rounding.

The8input files and cost data are hash-bound. Changed source/runtime/device
identities cannot silently adopt an old trajectory. The original journal refuses
uncertain spent calls and resumes only committed prefixes within20actual calls.
Native cycle caches use the official cache API under this checkout's `outputs/`,
not an undocumented home cache. Completed probes can be reused with zero new calls.

Public fresh Texas computation remains unavailable until its exact input pack can
be distributed. No private inputs were included in ordinary Git/model exports.
Do not shorten a demo and call it the original301-topology result.

## Historical GOC Configuration

`experiments/goc_500/configs/historical/` preserves the actual published and
training/evaluation configurations, separately labeled archival. Its original
population/scenario inputs and full legacy execution path are unavailable here;
the official-sample demo is not substituted for them. Cached results and supported
model inference remain usable without that historical population.

Training recipes and checkpoint ancestry are recorded, but raw training datasets
are not distributed here. Fresh retraining is not an advertised independently
qualified mode. See `artifacts/release_coverage.json` and the verification report
for exact tested models, platform, commands, and omissions.
