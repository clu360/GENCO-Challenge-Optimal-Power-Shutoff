# Public checkpoint archives

These immutable archives provide **15 model selectors / 14 unique weights** for
the GOC-500 and Texas2k adaptation testbed. They contain models, the GENCO
normalizer, and license notices. They contain no private Texas electrical inputs.

Use the [current main branch](https://github.com/clu360/GENCO-Challenge-Optimal-Power-Shutoff)
for code, four executed notebooks, retained results, the public IEEE14 GENCO
example, and the three-page submission. The model tag preserves its original
artifact cut; GitHub's automatic source ZIP for that older tag is not the latest
reproduction code.

After installing the pinned model environment, acquire both archives from the
repository root:

```sh
python scripts/download_models.py
genco-ops models --verify-hashes
genco-ops public-genco --output outputs/public_genco --execute
```

Local archives also work with `genco-ops acquire --bundle PATH`.

| Archive | Bytes | SHA-256 |
|---|---:|---|
| `genco_challenge_models_v149.zip` | 890,326,503 | `f15e6d6d21f906b6433e27590b01df831fbbc32c2d1457a7eba0b8fc3004eba7` |
| `opengridsfm_G500_v152.zip` | 60,987,194 | `36f6ef4d96e1f733c58f4f2cf5023323ba62f496fea693fe7dffa432cae63553` |

The supplement adds native G500 without replacing the primary archive.
Anonymous access to both ZIPs is verified. Complete archive/member checks and
all 15 official model loads were separately verified in an independent checkout.

All eight Texas fits are certified. Native GridSFM OPS/AC remains pending in the
publication cut, and Phase II stays held. Exact modified Texas electrical inputs
remain private; public weather-derived exposure and the small public GENCO
fixture are included in the source repository. This is a bounded reproducibility
release, not full historical campaign recomputation or a posted challenge entry.
