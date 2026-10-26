# Verification and remaining boundaries

The current refinement uses an independent GitHub clone in a short directory,
with separate Python 3.12 results-only and pinned CPU-model environments. Package
imports resolve inside that checkout. Candidate release files are copied into
that clone before verification; the development repository is not on its import
path. No PACE credentials, new training, or new AC solves are used.

## Current checks

| Check | Observed result |
|---|---|
| Fresh model acquisition | Both hosted archives downloaded, approximately 951 MB; archive size/SHA and all listed member hashes passed |
| Official model loading | All 15 catalog entries, representing 14 unique weights, loaded through the pinned official implementations |
| GOC numerical example | Four M0–M3 saved-case predictions and a new M2 bounded OPS demo with 16 actual model calls |
| Public GENCO numerical example | One real released-GENCO prediction on included public IEEE14 inputs |
| Notebooks | All four executed; notebook 01 embeds nine result figures, notebook 04 embeds its real prediction plot |
| Exact Texas inference/search probes | Eight modes explicitly unavailable because exact private electrical inputs were not recovered in this clone |
| Results-only test suite | 79 passed, three explicit model-related skips |
| Full pinned-model test suite | 82 passed, zero skips |
| Submission packet | Three pages, one embedded figure per page, no missing local links; rebuilt using only adjacent compact evidence |

See [acquisition verification](../artifacts/acquisition_verification.json),
[actual model/notebook execution](../artifacts/reproduction_verification.json),
and [final refinement checks](../artifacts/refinement_verification.json) for
machine-readable evidence, hashes, versions, and final test outcomes. Execution
locators in committed notebook outputs are sanitized; numerical arrays, measured
timings, statuses, and scientific hashes are preserved.

These model checks establish loading and bounded execution, not AC feasibility.
The public IEEE14 example does not reproduce Texas2k accuracy. The model-loading
check does not pretend to run a prediction for every checkpoint.

## Data and scientific scope

The official GENCO Texas release is a different grid: 2,000 buses/3,220 branches
versus the study's modified 2,751 buses/5,344 branches. The pinned
[identity check](../artifacts/official_texas_identity_check.json) records this.
Exact modified Texas electrical graphs/prepared inputs remain private. Public
weather-derived exposure is included and documented separately.

The official acquisition sources and all 750 ordered fingerprints for the GOC
held-out evaluation population are now identified. The recovery utility is
tested on small reconstruction/order/checksum fixtures. The full 2.406 GB source
archives have not been downloaded here and the 750-case replay is not qualified.
Historical GOC OPS baseline/PAC inputs remain distinct missing artifacts.

Eight Texas fits are certified; three GENCO Phase I searches and their selected
AC references are retained. Native GridSFM full OPS/AC remains pending in the
publication cut, and Phase II stays held. Full CUDA campaigns and independent
Julia AC numerical replay were not performed during this refinement.

## Reproduce the bounded checks

In the results environment:

```sh
python -m pytest tests -q
genco-ops verify
python scripts/execute_notebooks.py
python submission/build_submission.py
```

In the separately pinned model environment, after acquiring the artifacts:

```sh
python scripts/download_models.py
python scripts/check_models.py --output outputs/catalog_model_loading.json
python scripts/execute_notebooks.py --notebook 02_goc500_model_and_ops_demo.ipynb --notebook 04_public_genco_ieee14.ipynb --require-model-execution
```

Running all notebooks with `--models` also evaluates Texas asset availability;
completion with an unavailable numerical mode does not count as passed inference.
Use `--in-place` only when deliberately updating committed measured outputs.

## Earlier verification cuts

The original receipts remain available in `artifacts/release_verification.json`,
`published_executor_verification.json`, `native_g500_verification.json`, and
`hosted_release_verification.json`. They preserve earlier measured checks,
including historical private-input probes and native G500 certification. Their
test counts and input availability describe those dated environments, not the
current clean-checkout result. No old scientific receipt is rewritten to imply
that a newly unavailable private-input path passed again.

The GitHub repository and model release remain private. This is not a passed
public-access gate or a submitted Hugging Face entry. Public visibility requires
the author's approval and subsequent signed-out link verification. No private
electrical inputs are included in the candidate public files.
