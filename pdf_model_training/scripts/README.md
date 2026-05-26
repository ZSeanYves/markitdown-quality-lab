# Script Boundary Notes

## Current Tiny Fetch Script

`fetch_tiny_subsets.py` is a metadata-oriented helper only.

It is suitable for:

- tiny tracked metadata refresh;
- adapter sanity inputs;
- first-row or example-schema inspection.

It is not suitable for:

- full dataset acquisition;
- larger local-only teacher-training downloads;
- declaring a dataset ready for Task A teacher training.

## Future Local Acquisition Direction

If a future downloader is added for larger dataset pulls, it should:

- write only under `pdf_model_training/local_only/...`;
- avoid modifying tracked manifests automatically;
- record source, license, subset selection, and local hashes;
- remain separate from tiny tracked subset refresh logic.

## Training Boundary

Tracked scripts in this directory may help plan or document local-only flows,
but actual larger dataset payloads and teacher artifacts must remain outside git.
