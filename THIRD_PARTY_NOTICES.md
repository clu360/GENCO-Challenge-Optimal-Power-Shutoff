# Third-Party Sources

- GridFM GraphKit source: Apache-2.0, pinned commit
  `95b90eecc7f5c2c86a9dd776f0c3f40434def22f`.
  [Official repository](https://github.com/gridfm/gridfm-graphkit).
- GENCO OPF base: [official model card](https://huggingface.co/gridfm/genco-opf-datakit),
  Apache-2.0. Adapted weights retain parent hashes and the frozen normalization.
- Microsoft GridSFM source and Open checkpoint: MIT, pinned source commit
  `1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6`.
  [Source license](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/LICENSE)
  and [official model card](https://huggingface.co/microsoft/GridSFM_Open).
  The source license is retained under `docs/licenses/`.
- The GOC-500 bounded-demo input is the saved sample distributed with that exact
  Microsoft source revision. Its role is explicitly separate from the historical
  held-out evaluation populations. Original input provenance is retained.
- Raw modifiedTexas2k case/weather/graph inputs were supplied separately; their
  redistribution permissions have not been established here. Keep them private.

Model-card metadata and publication references were checked October25,2026.
No upstream performance claim is adopted as a measured result of this study.
No third-party paper PDF is redistributed.

## Verified References

Puech et al. (2026), *GENCO - A Unified Neural Solver Embedded in a Development
Framework for Steady-State Grid Analysis*, arXiv:2608.09921v2.
[Publication metadata](https://arxiv.org/abs/2608.09921).

Original OPS implementation/reference trail:
[PowerModelsWildfire.jl](https://github.com/WISPO-POP/PowerModelsWildfire.jl).
This study's loading-dependent exposure proxy and budgeted surrogate search are
modifications, not a claim to reproduce the original formulation unchanged.

Rhodes, Coffrin and Roald (2024), *Security constrained optimal power shutoff for
wildfire risk mitigation*, IET Generation, Transmission & Distribution18(18),
2972-2986, DOI10.1049/gtd2.13246.
[Institutional publication record](https://laro.lanl.gov/esploro/outputs/journalArticle/Security-constrained-optimal-power-shutoff-for/9916496160103761).
Security-constrained or higher-K extensions are not completed experiments here.
