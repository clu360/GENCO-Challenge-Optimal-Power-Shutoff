# GOC-500 Study

Retained Stage J FT3/FT4 search evidence and FT6 physical evaluations are under
`results/`. Model IDs `goc500.base`, `ft0`, `m1`, `m2`, `m3` are in the common
artifact catalog. FT0 is smoke-only; M2 and M3 are sibling adaptations from M1.

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
