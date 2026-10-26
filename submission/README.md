# Submission materials

The three-page [PDF](GENCO_Challenge_Submission.pdf) and equivalent
[Markdown](SUBMISSION.md) present GENCO as a testbed for grid-to-task adaptation
and physical verification, with wildfire-aware OPS as the application.
Texas/GENCO is the main experiment; GOC-500/GridSFM is the precursor.

From the repository root, in the results environment:

```sh
python -m pip install -e ".[paper]"
python submission/build_submission.py
```

The builder reads only `submission/data/`, `SUBMISSION.md`, and the adjacent
supplementary document. It regenerates three PNG/vector-PDF figures and the PDF,
checks input hashes, and verifies three pages, one figure per page, and local
links. It needs no original development checkout, model download, private
electrical inputs, cluster access, or numerical solves. These instructions also
work from the publication packet after installing numpy, pandas, matplotlib,
ReportLab, and pypdf.

`export_evidence.py` optionally rebuilds the compact tables from the larger
retained result tables **in this repository**. The figure builder does not need
that step. `data/provenance.json` binds source and compact-table hashes and
describes the populations; rounding is confined to presentation.

The supplementary GOC-500 report is useful for detailed prior methods and the
warm-start study. It is not required to understand the three-page entry. Its
older workshop and availability wording is addressed in the
[availability note](supplementary/AVAILABILITY_NOTE.md); the original report has
not been silently altered.

Repository and checkpoint downloads are public. Anonymous repository, README,
release-metadata, and ZIP-access checks passed on October 26, 2026; the
[receipt](../artifacts/public_release_verification.json) records their scope.
Exact modified Texas electrical inputs remain private. Figure attachments and the PDF must be uploaded
when posting to Hugging Face; relative local image paths alone will not render
in a Community discussion. No discussion is posted by this build process.

For real model execution, use the four notebooks and
[reproduction guide](../docs/reproduction.md), including the public IEEE14
GENCO example. That example is a compatibility demonstration; full Texas
performance requires the exact private electrical inputs. Generating this PDF
does not qualify the full historical campaigns as recomputed.
