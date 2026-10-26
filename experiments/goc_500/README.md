# GOC-500 Study

Select `goc500.base` (M0), `goc500.m1` (FullTop-1000), `goc500.m2`
(M1 + FullTop-500), or `goc500.m3` (M1 + N-1-500) through the same model
selector. M2 and M3 are sibling continuations. `goc500.ft0` is smoke-only.

Start with [notebook 01](../../notebooks/01_explore_published_results.ipynb)
for the executed result analysis and [notebook 02](../../notebooks/02_goc500_model_and_ops_demo.ipynb)
for real checkpoint inference and the bounded sample OPS example.

| Included evidence | Location | Population |
| --- | --- | --- |
| Accepted refined OPS study (FT7) | `results/refined_study/core_results/` | DC and M0-M3: 150,000 continuous evaluations, 7,500 topology rows, 75 finalists/A audits, 150 B-stage rows, 525 controlled warm-start solves |
| Refined derived analyses | `results/refined_study/derived/` | All five-lambda empirical fronts, AC discrepancies, state fidelity and warm-start summaries |
| Frozen M0 runtime study (RQ1) | `results/rq1/` | 54 unique fixed decisions from 75 provenance rows; per-repetition timings and paired summaries |
| Held-out physical evaluation (FT6) | `results/ft6_*.csv` | FullTop and N-1 populations, separate from the selected OPS decisions |
| Earlier study archive | `results/ft3_ft4/` | Original frozen evidence retained for provenance; use FT7 for the submission comparison |

The source/published hashes, row counts and exact numerical-column preservation
checks for FT7/RQ1 are in `artifacts/results_provenance.json`. Private text
locators are sanitized; scientific quantities are unchanged. Regenerate figures:

```bash
genco-ops results --study goc_500 --output outputs/goc500_results
```

`configs/historical/` preserves actual training/evaluation settings and the
hash-verified published FT3/FT4 RUN_CONFIG. These are explicitly archival, not
commands that secretly read the old development tree. The original search used
three scenarios, five lambda weights, topology budget100, five selected loads,
and twenty continuous evaluations. Do not replace it with Texas's301-state rule.

`configs/historical/frozen_pools/` includes the 30 original ordered pools for these
15 settings: 100 Guided candidates and 2 TH candidates per setting, 1,530 rows total.
Every CSV matches the original FT3/FT4 pool-copy receipt byte-for-byte; its public
manifest retains hashes, ranks and proxy scores without private filesystem paths.
These frozen candidates were reused across the original comparison, not discovered
again for each model. They are not Texas's model-specific hierarchical K2 pools.

The bounded executable example uses the official pinned sample under `data/`,
not the unavailable historical evaluation population. Run `genco-ops ops-demo
--model goc500.m1 --output outputs/new_goc_demo` after acquiring weights.
Its distinct identity, synthetic uniform hazard and small budget are recorded.

The original OPS runner reads this same upstream electrical sample; that does
not make its synthetic-uniform-hazard demo the historical OPS experiment. The
original prepared baseline-loading and PAC-freeze artifacts have not been
recovered, and the separate historical held-out evaluation population is absent.
Exact regeneration also needs the legacy executor, not the Texas 301-state path.
These full modes remain unqualified. The saved results, actual model loading,
and bounded sample demo are independent supported modes. No new GOC campaign is
launched.
