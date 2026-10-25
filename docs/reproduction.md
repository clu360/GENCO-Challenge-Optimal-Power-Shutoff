# Reproduction

## Results Without Models Or Solvers

Install `pip install -e '.[notebooks,test]'` in Python 3.12, then run:

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
genco-ops infer --model goc500.m1 --output outputs/goc500_inference
```

The bundle checksum and every member checksum are in `artifacts/model_bundle.json`.
A remote download URL is not invented: remote hosting remains a separate release
action. Models are genuinely included in the separately delivered local export.
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

## Full Historical Configuration

`experiments/texas2k/configs/phase_i_original.json` exports the actual recipe and
search settings, with explicit source/request identities. Loading it does not run
anything. It is not a full executor or a claim that the campaign was rerun here.
Full fresh Texas computation is unavailable publicly pending input permissions
and completion of the full historical executor port. The original research
checkpoint remains the versioned numerical execution source. Do not shorten a
demo and call it the original 301-topology result.

Training recipes and checkpoint ancestry are recorded, but raw training datasets
are not distributed here. Fresh retraining is not an advertised independently
qualified mode. See `artifacts/release_coverage.json` and the verification report
for exact tested models, platform, commands, and omissions.
