# GENCO for grid-to-task adaptation and physical verification

Select a checkpoint, inspect its results, and run the supported electrical-state
and optimal power shutoff (OPS) pipelines for **GOC-500** or **modified Texas2k**.
We study whether adaptation improves physical predictions and whether those gains
survive downstream AC decision audits.

GENCO-OPF and OpenGridFM's GraphKit are the Texas2k adaptation testbed. GOC-500
uses GridSFM as a separate precursor study. Grid, model and evaluation populations
remain explicit throughout the code and notebooks.

## Run GENCO on public inputs

After cloning this public repository, install the
[pinned CPU model runtime](docs/installation.md#official-cpu-model-runtime) and
acquire the public weights with `python scripts/download_models.py`. Then run
one actual GENCO-OPF prediction on the included IEEE14 inputs:

```sh
genco-ops public-genco --output outputs/public_genco --execute
```

[Notebook 04](notebooks/04_public_genco_ieee14.ipynb) contains executed outputs;
the [execution receipt](artifacts/reproduction_verification.json) records this
successful compatibility demonstration. It does not measure Texas performance.
The next section regenerates saved result figures; full Texas2k numerical
reproduction requires private electrical inputs and follows the
[reproduction guide](docs/reproduction.md).

## Start with the results

Use Python 3.12 in a short, writable checkout. See
[installation](docs/installation.md) for environment setup.

```sh
git clone https://github.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff.git
cd GENCO-Challenge-Optimal-Power-Shutoff
python -m pip install -e '.[notebooks,test]'
genco-ops results --study goc_500 --output outputs/goc500_results
genco-ops results --study texas2k --output outputs/texas2k_results
python scripts/execute_notebooks.py
```

These commands regenerate figures and summaries from included tables, without
checkpoints, GPU, Julia, a cluster account, or new scientific solves. New outputs
go under `outputs/`; accepted evidence stays intact.

| Notebook | Reader workflow |
|---|---|
| [01 Explore results](notebooks/01_explore_published_results.ipynb) | Adaptation, residuals, native frontiers, exact A/B outcomes and scoped timing for both grids |
| [02 GOC models and OPS](notebooks/02_goc500_model_and_ops_demo.ipynb) | Choose a GridSFM checkpoint; predict the official sample and run a bounded new search |
| [03 Texas models and OPS](notebooks/03_texas2k_model_and_ops_demo.ipynb) | Choose GENCO or GridSFM; inspect results and execute numerical paths when exact authorized inputs are installed |
| [04 Public GENCO example](notebooks/04_public_genco_ieee14.ipynb) | Load released GENCO-OPF and predict a small included public IEEE14 case |

Executed notebook outputs distinguish saved-result exploration, fresh prediction,
bounded demos and full historical recomputation. Missing numerical inputs are
reported as unavailable, never counted as successful inference.

## Select and acquire a model

The catalog has **15 entries / 14 unique weight files**, covering all certified
Texas fits and GOC adaptations. GOC's released base aliases the same native base
weight used by Texas. Intermediate G100 models preserve lineage; FT0 is smoke-only.

| Grid/family | Model selectors |
|---|---|
| GOC-500 GridSFM | `goc500.base`, `goc500.ft0`, `goc500.m1`, `goc500.m2`, `goc500.m3` |
| Texas GENCO | `texas2k.genco_opf.base`, `texas2k.genco_opf.G100`, `texas2k.genco_opf.G500`, `texas2k.genco_opf.G100_to_R400`, `texas2k.genco_opf.G100_to_W400` |
| Texas GridSFM | `texas2k.opengridsfm.base`, `texas2k.opengridsfm.G100`, `texas2k.opengridsfm.G500`, `texas2k.opengridsfm.G100_to_R400`, `texas2k.opengridsfm.G100_to_W400` |

The [catalog](artifacts/model_catalog.json) records weight/normalizer hashes,
ancestry, selection epochs and loader contracts. Install the separate
[pinned model environment](environments/model_cpu_requirements.txt), then run:

```sh
python scripts/download_models.py
genco-ops models --study goc_500
genco-ops models --study texas2k
```

Downloads verify archive size/SHA-256 and every member before extraction, using
existing GitHub authorization when required. Local archives also work with
`genco-ops acquire --bundle <file.zip>`. Large weights are release assets rather
than Git history. See [artifact acquisition](docs/artifacts.md).

## Run the selected pipeline

Use the same model selector in notebooks or the CLI. These commands execute real
CPU work; omitting `--execute` inspects the plan and missing assets:

```sh
genco-ops run --study goc_500 --model goc500.m2 --mode infer --output outputs/m2_inference --execute
genco-ops run --study goc_500 --model goc500.m2 --mode demo --output outputs/m2_ops_demo --execute
```

The GOC demo uses the included official electrical sample, two topologies and
16 actual model calls under synthetic uniform hazard. It is separate from the
published three-scenario experiment.

With an authorized Texas graph pack or prepared OPS input directory:

```sh
genco-ops run --study texas2k --model texas2k.genco_opf.G500 --mode infer --inputs /authorized/graphpack --output outputs/genco_prediction --execute
genco-ops run --study texas2k --model texas2k.genco_opf.G500 --mode published --inputs /authorized/prepared --device cpu --probe-topology '117;281' --output outputs/genco_probe --execute
```

The second command runs the original 20-call optimizer on one topology. The
original full 301-state CUDA search is a separate explicit mode, documented in
[reproduction](docs/reproduction.md). No command automatically submits cluster jobs
or starts training.

## Findings and interpretation

At equal 500-example Texas budgets, GENCO's selected Reference A normalized risks
are **1.1641 (G500), 1.0890 (Random), and 1.0891 (Wildfire)**. Sequential adaptations
select lower-risk, lower-shedding decisions than G500 here, but both choose the
same outage pair and all remain above baseline 1. Substantial worst-bus residuals
prevent interpreting these predictions as AC-feasible states.

G500's native-score advantage also changes after AC recovery: its selected
decision has native J = 1.0166 and audited J = 0.9319, versus
1.1601/0.8713 (Random) and 1.2091/0.8714 (Wildfire). These are each model's own
finalists, with different pair coverage and AC-recovered dispatch, rather than
a common-candidate ranking test.

GOC adaptation improves held-out fidelity and native-to-AC agreement, with
distribution-specific tradeoffs. Its paired fixed-decision benchmark measures
3.59× faster released-GridSFM evaluation; the separate warm-start study shows
about 2.2% mean IPOPT savings. These are not complete GENCO/Texas OPS speedups.

See the [methodology](docs/methodology.md),
[limitations](docs/results_and_limitations.md) and
[verification](docs/RELEASE_VERIFICATION.md) for evidence and timing boundaries.

## Data coverage

| Material or mode | Status |
|---|---|
| Published tables and figure regeneration | Included: GOC FT6/FT7/RQ1 and Texas K/L/M accepted evidence |
| Catalogued models and normalizers | Checksum-bound release archives with acquisition commands |
| GOC sample inference and bounded OPS | Included official sample and real adapters |
| Public GENCO compatibility example | Included official IEEE14 sample and released-checkpoint adapter |
| Full GOC held-out population | Official acquisition recipe and all 750 ordered fingerprints; full recovery/replay not reverified |
| Texas weather-derived exposure | Public derivative with date, source and preprocessing provenance |
| Exact modified Texas electrical inputs/graphs | Private; the official GENCO Texas data is a different grid |
| Full campaigns and training populations | Per-dataset acquisition and qualification in the data manifest |

The official GENCO contingency release has 2,000 buses and 3,220 branches; our
modified case has 2,751 buses and 5,344 branches. The
[identity check](artifacts/official_texas_identity_check.json) records its pinned
source and comparison. Public weather does not imply permission to redistribute
the different electrical case. See [data coverage](artifacts/data_catalog.json).

Eight Texas fits are certified. Native GridSFM full OPS/AC remains pending in the
publication cut; Phase II is held. Higher-K screening and risk-aware shortlist
refinement remain proposed experiments.

The [three-page submission](submission/SUBMISSION.md),
[PDF](submission/GENCO_Challenge_Submission.pdf), and
[standalone publication builder](submission/README.md) use included compact
evidence. Code and checkpoint archives are public, with
[anonymous access verified](artifacts/public_release_verification.json).
Exact modified Texas electrical inputs remain private.

## Extend the workflow

`src/genco_ops/` contains shared selectors, numerical adapters and reporting.
`experiments/goc_500/` and `experiments/texas2k/` separate frozen configurations,
data and results. `artifacts/` binds their identities; notebooks call shared code.

Start with `genco_ops.catalog.models` and `genco_ops.workflow.run_workflow`.
Use a new output directory per experiment, retain input/model hashes, and label
changed budgets/hazards as new studies. Upstream attribution and licenses are in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
