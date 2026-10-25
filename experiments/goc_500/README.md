# GOC-500 Study

Retained Stage J FT3/FT4 search evidence and FT6 physical evaluations are under
`results/`. Model IDs `goc500.base`, `ft0`, `m1`, `m2`, `m3` are in the common
artifact catalog. FT0 is smoke-only; M2 and M3 are sibling adaptations from M1.

`configs/historical/` preserves actual training/evaluation settings and the
hash-verified published FT3/FT4 RUN_CONFIG. These are explicitly archival, not
commands that secretly read the old development tree. The original search used
three scenarios, five lambda weights, topology budget100, five selected loads,
and twenty continuous evaluations. Do not replace it with Texas's301-state rule.

The bounded executable example uses the official pinned sample under `data/`,
not the unavailable historical evaluation population. Run `genco-ops ops-demo
--model goc500.m1 --output outputs/new_goc_demo` after acquiring weights.
Its distinct identity, synthetic uniform hazard and small budget are recorded.

Exact regeneration of the historical full GOC campaign requires its original
scenario/population inputs and legacy search execution path, which are not
qualified in this release. The saved results, actual model loading, and bounded
sample demo are independent supported modes. No new GOC campaign is launched.
