# Modified Texas2k Study

Historical K/L tables and Stage M Phase I results remain separate under `results/`.
The actual Phase I case is Scenario16 with the June23,2023 4PM CDT cumulative
environmental snapshot, squared apparent loading and stored risk normalization.

The original Phase I numerical implementation is exported to
`genco_ops.published`, with source hashes and scoped AST-definition checks.
`configs/phase_i_original.json` seals the physical prepared-input hashes, eight
fit recipes and original50-K1/five-parent/up250-K2, alpha-only20-call search.

The `phase-i-ops` command validates without executing by default. Full execution
requires an explicit CUDA device; CPU is allowed only for a separately identified
single-topology portability probe. Checkpoint-resident scoring, physical-state
exports, original journal replay and reference-finalist selection are reused.
No Slurm jobs are submitted by this command.

Authorized input packs are not public pending redistribution verification.
Neither their absence nor pending native searches is replaced by a different
physical case or a fabricated successful result. See `docs/reproduction.md`.
