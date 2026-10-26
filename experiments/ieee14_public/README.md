# Public GENCO example: IEEE14

This small example runs the actual GENCO-OPF architecture on an entirely public
electrical fixture. It uses the original GraphKit normalization and OPF masks,
one real model call, and no AC solver or private Texas inputs.

The ten raw Parquet files (249 KB) are copied from the official GraphKit test
fixture at commit `95b90eecc7f5c2c86a9dd776f0c3f40434def22f`. Their Git blob
SHA-1 values were checked against that public commit's GitHub tree; SHA-256
checksums, source paths, byte counts and provenance are in `data_manifest.json`.
GraphKit's Apache-2.0 license applies; see `docs/licenses/GraphKit-Apache-2.0.txt`.

After acquiring the model bundle and installing the model environment, run
[notebook 04](../../notebooks/04_public_genco_ieee14.ipynb), or:

```python
from pathlib import Path
from genco_ops.public_genco_demo import run_public_demo

result = run_public_demo(Path.cwd(), Path('outputs/public_ieee14'))
```

This example uses only the released GENCO-OPF checkpoint. Its IEEE14 predictions
demonstrate compatibility, **not held-out accuracy, an adaptation advantage, Texas2k
reproduction, an OPS result, or AC feasibility**. No IEEE14 fine-tuning was run.
The released normalizer is loaded unchanged; it is not refitted to this fixture.

Raw input copies, official processed graphs, normalized prediction tensors and
decoded bus/generator CSVs are written under `outputs/`. The packaged fixture
and model weights remain immutable.
