# Models and data

Small inputs and scientific result tables live in Git. Large checkpoints are
checksum-bound release assets. Exact modified Texas electrical inputs are private
and are not silently replaced with another Texas grid.

## Acquire the models

After [installing the CPU model environment](installation.md), run from the
repository root:

```sh
python scripts/download_models.py
genco-ops models --study goc_500 --verify-hashes
genco-ops models --study texas2k --verify-hashes
```

The downloader acquires two archives, approximately **951 MB** in total, from
the pinned [model release](https://github.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff/releases/tag/phase-i-models-v152).
It checks the release asset's byte count and digest, the complete archive SHA-256,
and every member before installation. Existing matching archives under `dist/`
or `outputs/downloads/` are reused. Different existing files are not overwritten.

Access follows repository visibility. For private access, use an existing
authorized Git credential or set `GH_TOKEN`/`GITHUB_TOKEN` in your environment;
never put a token in a notebook or command argument. Git credential lookup is
noninteractive. No `gh` installation is required. Credentials are not written
to acquisition receipts or passed to redirected asset hosts.

Local copies of either archive work without network access:

```sh
genco-ops acquire --bundle /path/to/genco_challenge_models_v149.zip
genco-ops acquire --bundle /path/to/opengridsfm_G500_v152.zip
```

The primary archive contains the original thirteen unique weights, the GENCO
normalizer, and notices. The supplement adds the certified native G500 weight
and its notice. Together they serve **15 catalog entries / 14 unique weights**:

| Model group | Selectors |
|---|---|
| GOC GridSFM | `goc500.base`, `goc500.ft0`, `goc500.m1`, `goc500.m2`, `goc500.m3` |
| Texas GENCO | `texas2k.genco_opf.base`, `.G100`, `.G500`, `.G100_to_R400`, `.G100_to_W400` |
| Texas GridSFM | `texas2k.opengridsfm.base`, `.G100`, `.G500`, `.G100_to_R400`, `.G100_to_W400` |

Expand the abbreviated Texas suffixes using the prefix in the same row. GOC's
base aliases the native released base. G100 preserves intermediate ancestry;
FT0 is a smoke adaptation, not a reported final competitor. The
[complete catalog](../artifacts/model_catalog.json) records exact hashes,
epochs, parent identities, normalization, and loader contracts.

A fresh independent clone downloaded both complete archives and verified all
members in approximately 267 seconds. This is acquisition time, not model
inference or OPS timing. The [receipt](../artifacts/acquisition_verification.json)
records the actual check; it does not claim private-data or full-campaign replay.

## Data coverage

| Data | Availability and role |
|---|---|
| Published GOC and Texas tables | Included; regenerate figures and inspect accepted results |
| Official GOC electrical sample | Included; actual single-case prediction and bounded new OPS demonstration |
| Public GraphKit IEEE14 fixture | Included; GENCO interface example separate from the reported Texas experiment |
| Texas weather-derived `p_env` | Included for 5,344 physical branches; frozen June 23, 2023 exposure |
| Exact modified Texas graphs and prepared electrical inputs | Private; hashes and expected filenames are recorded |
| Historical 750-case GOC FT6 population | Official sources and ordered fingerprints identified; recovery utility provided, full recovery/evaluation not performed |
| Historical GOC OPS baseline/PAC inputs | Not recovered; the sample demo does not stand in for them |
| Full adaptation training populations | Not bundled; checkpoint lineage and training configurations are retained |

[The data catalog](../artifacts/data_catalog.json) separates these populations.
Public weather provenance and the coefficient CSV are under
[`experiments/texas2k/data/weather/`](../experiments/texas2k/data/weather/README.md).
These coefficients preserve the evaluated exposure input; they are not a raw
weather-grid redistribution or a newly calibrated ignition probability.

## Why the Texas inputs stay separate

The official GENCO contingency dataset inspected at a pinned revision contains
2,000 buses and 3,220 branches. Our modified Scenario 16 case has 2,751 buses and
5,344 branches. Its electrical identities therefore cannot be supplied by
substituting that public dataset. The
[source comparison](../artifacts/official_texas_identity_check.json) records the
downloaded official shard, hashes and observed dimensions. Public weather
availability does not establish permission to redistribute the different grid.

For an authorized local installation, the graph pack can mirror the catalog's
`artifacts/private_inputs/texas2k/` tree or contain its named `.pt` fixtures.
`infer --inputs` changes the location, not the required input SHA. The original
numerical OPS path instead needs the prepared Parquet files and
`input_contract.json` under a supplied directory.

`scripts/package_authorized_inputs.py` can export already authorized local files
to an ignored ZIP and create a checksum-bound `artifacts/input_bundle.json`:

```sh
python scripts/package_authorized_inputs.py --dataset texas2k.authorized_inputs
# Or export just the original nine-file OPS input pack:
python scripts/package_authorized_inputs.py --dataset texas2k.ops_inputs
```

The utility does not download or upload private inputs. A ready-to-download
private input bundle is not distributed in this release. Its manifest and ZIP,
if created by an authorized provider, can be installed using the same `acquire`
command. Access approval is not inferred from the presence of a checksum.
