# PDF Text-Flow Assist Model

This directory contains offline-only assets for the PDF text-flow assist model
research track.

The goal is not to replace the checked rule system. The goal is to support it
with local-only training and evaluation assets that can later be connected, if
ever, behind explicit rule gates and fail-closed runtime behavior.

Tracked assets here include:

* `manifest.tsv` and draft task-aware manifest files
* `labels/` with manual local label TSVs
* `scripts/` for feature export and local-only train/eval helpers
* `datasets/` for tracked metadata or tiny subsets
* `models/` for historical model JSON snapshots
* `reports/` and `evaluation/` for local-only notes and outputs
* `archive/` for migration notes and legacy references

Normal PDF conversion in the main repository does not depend on these assets.
Current checked behavior remains rule-first MoonBit logic in `convert/pdf`.

## Model Scope

This lab is for a PDF text-flow assist model family, not a single flat layout
classifier.

The intended task split is:

* `Task A: convert_block_classification`
  * layer: `convert/pdf`
  * purpose: assist convert-layer mapping from PDF line/block text flow to
    Markdown / IR semantics such as paragraph, heading, caption, table-like,
    form-row, list-item, separator, link-text, keep-as-text, and
    footer/header noise
* `Task B: parser_boundary_assist`
  * layer: `doc_parse/pdf/text` or parser/layout bridge
  * purpose: assist parser-layer decisions around cross-page boundaries,
    low-signal transitions, and reading-order risk
* `Task C: parser_layout_signal_assist`
  * future target only
  * purpose: low-signal or scanned-ish parser/layout signals; not part of the
    current training path

Boundary labels do not belong in the same flat label space as convert-layer
block labels. Task B should remain separate from Task A training/eval.

## Current Focus

Near-term work in this directory is intentionally narrow:

* keep feature export healthy for current tracked samples
* keep schema and manifest drafts aligned with the intended task split
* focus first on `Task A: convert_block_classification`
* keep `Task B` tracked separately and do not mix boundary labels into block
  label training
* leave `Task C` as future-only design scope

Current non-goals:

* no runtime model integration
* no PDF OCR integration
* no automatic rule replacement
* no production claim based on local-only held-out checks

Historical `models/*.json` files remain useful as migration artifacts and
historical metadata only. They should not be treated as proof of the current
best model target, schema, or eval policy.

## Script Entrypoints

Preferred local-only entrypoints currently live here:

* `scripts/export_manifest_features.py`
* `scripts/local_eval.py`
* `scripts/train.py`
* `scripts/fetch_tiny_subsets.py`
* `scripts/export_features.sh`
* `scripts/evaluate.sh`

These scripts assume:

* the main repository lives one directory above this lab
* the external quality corpus payloads live in `../external_quality`
* the main repository still provides the native MoonBit export/infer tool

Typical feature-export smoke:

```bash
python3 markitdown-quality-lab/pdf_model_training/scripts/export_manifest_features.py \
  --manifest markitdown-quality-lab/pdf_model_training/manifest.tsv \
  --corpus-root markitdown-quality-lab/external_quality \
  --sample-id heading_basic \
  --output-dir .tmp/pdf_model_training/post_migration_smoke
```

This directory is for local research and schema work only. Any future runtime
connection must remain gated by deterministic rules and fail closed when model
support is absent, weak, or intentionally disabled.

## Data Scale And Training Route

The current intended route is no longer "tiny subset as the main training
strategy".

The updated route is:

1. keep tracked metadata, mapping files, and tiny sanity fixtures in git;
2. keep larger public dataset payloads local-only;
3. use larger local-only Task A corpora for offline teacher training and
   evaluation;
4. distill the teacher results into rule suggestions, lightweight classifier
   candidates, confidence thresholds, and feature-level explanations;
5. evaluate any future runtime candidate separately under fail-closed rule
   gates.

This means:

* training-time assets may be large and slow, but stay local-only;
* runtime-time assets, if ever adopted, must stay lightweight;
* teacher models are not runtime artifacts;
* tiny tracked subsets are for adapter/schema sanity only, not for claiming
  enough coverage for production-grade Task A training.
