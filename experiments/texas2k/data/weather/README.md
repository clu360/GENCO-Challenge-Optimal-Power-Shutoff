# Frozen public weather-derived exposure

`scenario16_environmental_exposure.csv` contains the frozen environmental
coefficient `p_env` for all 5,344 physical branches, including the 3,993
switchable transmission lines. The authors confirmed that the weather source
is public. This small derivative contains branch identities and exposure only;
electrical parameters and baseline loading remain separate inputs.

The snapshot is **June 23, 2023, 16:00 CDT (21:00 UTC)**. Stage K maps its
`hazard_score_p_cumulative` cumulative Fosberg Fire Weather Index exposure to
`p_env`. Phase I multiplies this coefficient by squared apparent-power loading
and sums over energized switchable transmission lines. It is an exposure proxy,
not a calibrated ignition probability.

`source_manifest.json` records the exact source and exported-file hashes. The
coefficients are copied from the accepted canonical branch table without
recomputing weather or changing the snapshot. This preserves the evaluated
weather input for result inspection and authorized recomputation.

The original weather workflow used PowerWorld weather exports. The development
tree's `POWERWORLD_WEATHER_EXPORT_README.md` also describes a **June 25** preview;
that preview is a different dataset and must not replace this June 23 snapshot.
This package does not claim to contain the original raw weather grid or the
full weather-to-branch preprocessing inputs.

The challenge's released Texas grid is a different electrical case from the
modified grid evaluated here; see
[`official_texas_identity_check.json`](../../../../artifacts/official_texas_identity_check.json).
Public weather availability does not make those electrical inputs identical.
