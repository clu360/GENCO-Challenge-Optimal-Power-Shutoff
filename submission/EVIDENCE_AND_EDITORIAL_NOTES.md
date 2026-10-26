# Evidence and editorial decisions

The author selected the audit's second framing: GENCO as a testbed for
grid-to-task adaptation and physical verification, using wildfire OPS as the
motivating downstream task. The submission leads with GENCO/Texas; the separate
GridSFM/GOC-500 study supplies methodological context and scoped timing evidence.

- The three Texas strategies have the same 500-example budget. This comparison
  does not establish improvement over the released GENCO checkpoint.
- Physical validation uses 100 cases per G/R/W distribution. Historical code O
  maps to wildfire W; each row in the compact table records the sample count.
- Mean worst-bus P imbalance is explicit. Small average errors are not a
  certificate of AC feasibility.
- Reference A fixes each model's selected topology/service; it optimizes economic
  AC dispatch. The R and W finalists share the same pair. Their risks remain
  above the stored intact baseline.
- Across these own finalists, G500 has the lowest native J but the highest
  Reference A J. This changes the cross-model ordering; it is not a common-pool
  rank-agreement result. Reference A replaces predicted dispatch, and K2 coverage
  differs by evaluator. GENCO's accepted Phase I search minimizes J directly;
  its recorded physics penalties are diagnostics, not added search penalties.
- Reference B maximizes total service and then minimizes cost at that total
  service. It may reallocate served demand. The retained B policy relaxes online
  generator active-power minima to zero; it is not an identical-constraint
  comparison with Reference A and is not risk-constrained recourse.
- GOC aggregate fidelity compares each model's own selected decisions over 15
  common scenario/weight settings. It is not a matched-input prediction test.
- The 54-decision paired CPU timing study concerns released GridSFM M0. It is
  distinct from fine-tuning, warm starts, and Texas/GENCO production runtime.
- GOC's nominal 100 topology attempts include a duplicate topology in some
  pools; this is not represented as 100 distinct physical topologies everywhere.
- The proposed shortlist/risk-aware AC refinement and higher-K studies are future
  work. No deadline-driven training or new OPS campaign was performed.

`data/provenance.json` identifies retained inputs and compact exports by SHA-256.
The compact data contain no model predictions newly generated for this paper.
The public IEEE14 GENCO demo verifies a runnable interface; it does not replace
the private Texas electrical case or reproduce its reported performance.

The original GOC report remains unchanged as supplementary detail. Its current
availability note accompanies it. Code and model archives were made public with
author approval; anonymous access checks passed on October 26, 2026. The reachable
Git history and release-member inventory were checked for private inputs before
publication. Exact Texas electrical inputs remain excluded. No Hugging
Face discussion or external message has been posted.
