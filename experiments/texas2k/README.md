# Modified Texas2k Study

Historical K/L tables and Stage M Phase I results remain separate under `results/`.
The actual Phase I case is Scenario16 with the June23,2023 4PM CDT cumulative
environmental snapshot, squared apparent loading and stored risk normalization.

Use [notebook 01](../../notebooks/01_explore_published_results.ipynb) to inspect
the executed analysis of recorded results and [notebook 03](../../notebooks/03_texas2k_model_and_ops_demo.ipynb)
to select all six final models, predict a saved case, and run an explicitly
bounded original-contract probe for either model family.

The selectors are `texas2k.genco_opf.<regime>` and
`texas2k.opengridsfm.<regime>`, where the final regimes are `G500`,
`G100_to_R400`, and `G100_to_W400`. `G100` is an intermediate checkpoint.
Historical GENCO-PF transfer/contingency outcomes remain in the Stage L result
tables. Those are separate baseline experiments, not the Phase I fine-tuned
OPF checkpoints in the current model catalog.

| Included evidence | Location | Completion boundary |
| --- | --- | --- |
| Certified fit inventory | `results/stage_m/tables/fine_tuning_inventory.csv` | Eight accepted fits |
| Per-case physical validation | `results/stage_m/tables/physical_validation.parquet` | 2,100 rows across seven checkpoints; native G500 per-case metrics absent locally |
| Topology/continuous trials | `results/stage_m/tables/candidate_results.parquet`, `continuous_evaluations.parquet` | Three GENCO searches: 903 topology rows and 18,060 continuous calls |
| Selected decision AC A/B | `results/stage_m/tables/finalist_native_and_exact.csv` | Three GENCO finalists; native full OPS/AC remains pending |
| Retained physical finalist state | `results/stage_m/retained_decisions/` | Recompute risk/service/objective without new model predictions |
| Historical control/search comparisons | `results/stage_k/`, `results/stage_l/` | Different control policies and runtime boundaries; partial comparability |

```bash
genco-ops results --study texas2k --output outputs/texas2k_results
genco-ops models --study texas2k
```

The original Phase I numerical implementation is exported to
`genco_ops.published`, with source hashes and scoped AST-definition checks.
`configs/phase_i_original.json` seals the physical prepared-input hashes, eight
fit recipes and original50-K1/five-parent/up250-K2, alpha-only20-call search.

The `phase-i-ops` command validates without executing by default. Full execution
requires an explicit CUDA device; CPU is allowed only for a separately identified
single-topology portability probe. Checkpoint-resident scoring, physical-state
exports, original journal replay and reference-finalist selection are reused.
No Slurm jobs are submitted by this command.

Public weather availability is separate from the exact electrical input pack.
The original electrical/prepared pack still needs its own verified acquisition
route and redistribution check.
Neither their absence nor pending native searches is replaced by a different
physical case or a fabricated successful result. See `docs/reproduction.md`.
