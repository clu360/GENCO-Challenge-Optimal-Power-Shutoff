# Release Verification

## Actual Supported Checks

An isolated Git clone outside the original development tree was installed into
two separate Windows/Python3.12.11 environments. The basic environment has no
Torch installed. Package imports were checked to resolve inside that checkout;
no original research import or PACE credentials were used.

- Results-only suite: 26 passed, two model tests explicitly skipped.
- Pinned official-model environment: 28 passed, including real bounded model calls.
- All three notebooks execute from fresh kernels. The Texas notebook explicitly
  marks missing private input UNAVAILABLE, not a numerical pass.
- Fourteen catalog entries (thirteen unique weight files) genuinely load through
  official packages; GOC base is an alias of the native released base.
- A new GOC example performs16 actual calls over two topologies. It uses a distinct
  demo identity and synthetic uniform hazard, not the historical geographic case.
- All three Texas GENCO saved finalists' native/AC risk, service, objective and
  line identities recompute from retained derived physical-state diagnostics.
- The actual Julia A/B numerical source and command mapping are exported. Its
  independent numerical run is untested; no solver or AC-feasibility claim is made.
- A Windows checkout line-ending mismatch was caught and repaired by preserving
  exact stored artifact bytes. Failed early checks remain private audit evidence.
- AC preparation now refuses nonempty evidence directories before writing.
  Notebook outcome reporting follows actual structured output instead of a fixed skip.

Actual commands, exit statuses, runtimes, stdout/stderr hashes, package versions,
official Git source commits and checkpoint hashes are in
`artifacts/release_verification.json`. These bounded execution times are not
training/production speedup or billing estimates. Notebook TCP/Windows event-loop
warnings were retained; execution completed. Scientific settings were not changed.

## Reproduction Commands

```sh
python -m pip install -e '.[notebooks,test]'
python -I scripts/verify_release.py
```

In the separately pinned official-model environment, after explicit acquisition:

```sh
genco-ops acquire --bundle genco_challenge_models_v149.zip
python -I scripts/check_models.py --output outputs/catalog_model_loading.json
python -I scripts/verify_release.py --models
```

## Completion Boundaries

This is a verified results/bounded-demo checkpoint, not a fully passed submission
gate, full historical recomputation, remote publication, challenge-form submission
or full Phase I completion. Full historical executor portability and public Texas
input permission remain unresolved. Local model-bundle acquisition is verified;
no fictitious public asset URL is supplied. Native G500/OPS/AC remain pending and
Phase II remains held. Pending results will be added in separate verified commits.
