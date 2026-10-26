# Findings and limits

This is an adaptation and physical-verification testbed for downstream wildfire
shutoff screening. It examines when better grid-state predictions lead to better
audited operating decisions. It does not establish a solved OPS problem or a
universally superior model.

## What the experiments show

**GOC-500** is a controlled precursor study using GridSFM, constructed hazard
scenarios and shared frozen topology pools. Adaptation improves several held-out
prediction and native-to-AC agreement measures, with distribution-dependent
tradeoffs. Useful below-baseline AC-audited risk decisions occur, although large
S1/S3 reductions already exist with the released model. FT6 prediction/physics
evaluation, FT7 downstream audits and RQ1 evaluator timing retain distinct data
and timing scopes.

**Modified Texas2k** tests GENCO-OPF and native GridSFM adaptation under a
geographic environmental snapshot. All eight Phase I fits are certified. Three
GENCO final checkpoints have complete 301-topology searches and designated
Reference A/B audits. Reference A normalized risks are **1.164144 (G500),
1.089042 (G100 to Random), and 1.089060 (G100 to Wildfire)**. Random/Wildfire
select the same outage pair but different service decisions. All remain above
the stored baseline of 1 while shedding some demand: this completed GENCO subset
does not demonstrate an improved risk/service outcome against that baseline.

Native GridSFM full OPS/reference branches remain pending in this publication
cut. Fit certification is separate from completed downstream evaluation.
Phase I is not declared complete; Phase II is held.

The two grids address a common adaptation-to-decision question, but their
hazards, model families, training distributions, controls and search designs
differ. Their results do not isolate grid size or support a pooled model ranking.

## Physical and operating interpretations

Prediction error, physical consistency and decision quality are separate
quantities. Logged training physics loss aggregates layers and is not a nodal
MW/MVAr residual or an AC feasibility certificate. Smaller mean residuals can
coexist with severe worst-bus errors and line overloads. Validation on fixed
cases does not replace physical audits of selected K1/K2 operating states.

Risk is a loading-dependent environmental exposure proxy, not a calibrated
ignition probability. Reference A is economic AC redispatch at fixed selected
topology and service; it need not preserve a risk-aware dispatch's risk.
Reference B recovers maximum service at that topology and then economic dispatch;
it imposes no wildfire-risk ceiling. Its higher-service point is not evidence
that the original low risk can be retained, nor proof that such a compromise is
impossible. Connecting A and B endpoints does not trace a Pareto frontier.

Historical Texas DC/AC results show that continuous dispatch and service choices
matter substantially: large risk reductions accompany substantial curtailment,
and maximum-service economic recovery loses much of that reduction. This is
evidence for controlled decomposition, not an isolated causal estimate of
topology versus continuous control. Stored baseline loading and recovered
economic AC states also have different operating definitions.

## What users can reproduce now

Included tables support figure/result regeneration without models or solvers.
All catalogued weights have public checksum-bound acquisition; a fresh independent
clone actually downloaded and verified both complete archives before publication.
[Signed-out access](../artifacts/public_release_verification.json) was subsequently
verified without distributing private Texas electrical inputs. The included GOC
sample supports real model inference and a separately identified bounded new
OPS demonstration. Public IEEE14 supports a real GENCO interface example, with
no claim of Texas reproduction, adaptation gain or AC feasibility.

Texas weather-derived exposure is public and included. The exact modified
electrical case and dependent graphs remain private: the official GENCO Texas
release is a different grid. An authorized prepared pack can exercise the
exported original executor. Full CUDA recomputation, fresh retraining and
independent numerical Julia AC execution are not qualified release modes.

The original GOC FT6 750-case population now has official acquisition sources,
ordered fingerprints and an explicit recovery utility. Full archive recovery
and numerical evaluation replay have not been performed. The separate historical
OPS baseline/PAC inputs remain unrecovered. The public one-case demo is not
substituted for either population.

See [artifact coverage](../artifacts/data_catalog.json),
[reproduction commands](reproduction.md) and
[verification](RELEASE_VERIFICATION.md) for exact evidence boundaries. A script
that executes while reporting unavailable inputs is not a passed numerical run.

## Runtime and extensions

RQ1's paired fixed-decision benchmark and the separate GOC warm-start study
measure evaluator and solver stages, respectively. Inference/initialization,
training, search and final AC audits have different accounting scopes.
Historical Texas cross-hardware timing is implementation evidence, not a
matched end-to-end speedup at equivalent feasible solution quality.

Higher-K screening, broader topology coverage, and risk-aware AC refinement of
a surrogate shortlist remain proposed experiments. Existing A/B audits do not
establish shortlist recall, rank agreement with risk-aware AC optimization,
global optimality, or an end-to-end GENCO runtime advantage. No causal
architecture advantage or challenge submission is claimed.
