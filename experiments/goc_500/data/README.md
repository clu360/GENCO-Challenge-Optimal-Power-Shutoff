# GOC-500 inputs and the exact evaluation population

`case500_goc.pyg.json` is the small, pinned official GridSFM example used by the
bounded notebook demo. It is a different population from the historical FT6
held-out evaluation and does not reproduce the published validation metrics.

The **source and identities for the historical 750 graphs are available**.
[`evaluation_population.json`](evaluation_population.json) contains the original
ordered tensor fingerprints for 375 FullTop and 375 N−1 test graphs, the official
Google OPFData source objects, and their immutable generation, byte count, and
CRC32C checksums. The retired local processed cache is absent. This release has
not downloaded those large archives or rerun the full held-out evaluation.

The inputs come from Google DeepMind's OPFData through the official
[GridSFM adapter at the recorded commit](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/opfdata_train.py),
which wraps [PyG's OPFDataset](https://github.com/pyg-team/pytorch_geometric/blob/2.8.0.post1/torch_geometric/datasets/opf.py).
The original environment used PyTorch 2.8.0 CPU, PyG 2.8.0.post1, seed 42, and
evaluation batch size 8. These historical pins differ from the portable one-case
model environment; reproduction of historical metrics needs the original
evaluation implementation and environment as well as the recovered graphs.

## Inspect or recover the data

Run from the repository root. The default command only prints a plan:

```bash
python scripts/recover_goc500_evaluation_data.py
```

Two group-zero archives are required, **2,406,018,938 bytes total** before
decompression. Downloading is explicit. The optional recovery dependency makes
the large-file CRC32C verification faster:

```bash
python -m pip install -e ".[recovery]"
python scripts/recover_goc500_evaluation_data.py --download
python scripts/recover_goc500_evaluation_data.py --prepare
```

Planning and downloading do not require a model environment. **Preparation
requires PyTorch and PyG**, installed through the documented model environment;
checkpoint weights are unnecessary. The SHA256 identity gate prevents a different
package version or processing convention from silently changing the population.

Alternatively, put the official, checksum-matching archives at
`outputs/goc500_evaluation_data/downloads/fulltop.tar.gz` and `n1.tar.gz`, then
run only `--prepare`. `--output /path/to/fresh/directory` chooses another output
location. No source files, model weights, or existing prepared population are
overwritten. An incomplete `.part` file is preserved for inspection.

The downloader requests the recorded GCS object generation and checks the byte
count and CRC32C. Preparation reads the JSON records directly from the archives,
reconstructs the original untransformed PyG schema including GridSFM's feasible
label, and matches **every selected graph's tensor SHA256**. It writes only:

- `prepared/fulltop.pt` and `prepared/n1.pt`: 375 graph dictionaries each in the
  historical order, readable with `torch.load(..., weights_only=True)` and
  `HeteroData.from_dict(...)`.
- `recovery_receipt.json`: archive checksums, selected raw member names, and
  each ordered graph fingerprint.

Preparation generates no new power-flow labels and runs no training, model
inference, OPS search, or AC solver. A successful recovery is a verified input
population, not a claim that the historical metrics have been recomputed.

## Why matching by fingerprint matters

The historical PyG loader enumerated raw files with `os.listdir`, whose order
depends on the filesystem. A fresh cache's first 375 rows therefore need not be
the same 375 evaluated originally. The recovery utility examines all 750 test
records in each official shard, identifies the saved fingerprints, and restores
their recorded order. It stops if any fingerprint is missing or ambiguous.

This recovery covers FT6's prediction/physics evaluation population. The
historical OPS study's baseline input, calibrated PAC ingredients, and raw
candidate execution state are separate dependencies; recovering FT6 data alone
does not reproduce the full Stage J OPS search.
