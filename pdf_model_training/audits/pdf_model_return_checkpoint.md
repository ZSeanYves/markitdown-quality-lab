# PDF Model Return Checkpoint

Date: 2026-05-31

## Decision

External-quality expansion is complete enough for the next PDF model-training
turn. The current converter and quality baseline is clean, so offline
`text_block_classifier` / `layout_recovery_model` training and evaluation can
resume.

This is not runtime approval. Model runtime integration remains paused, and no
runtime hook should be proposed from this checkpoint alone.

## Current Validation Baseline

Main sample validation:

* `bash samples/check.sh --manifest-only`: passed
* `bash samples/check.sh`: passed all 9 stages
  * Markdown: 444 passed / 0 failed
  * metadata: 85 passed / 0 failed
  * assets: 90 passed / 0 failed
* `moon check`: passed
* `bash samples/bench.sh --help`: passed

External quality validation:

* `bash samples/check_quality.sh`: 315 ready rows passed / 0 failed / 1
  skipped / 0 expected-fail
* `bash samples/check_quality.sh --format pdf`: 79 ready rows passed / 0
  failed / 1 skipped / 0 expected-fail
* per-format quality checks are green for:
  * csv
  * docx
  * epub
  * html
  * json
  * markdown
  * pdf
  * pptx
  * txt
  * xlsx
  * xml
  * yaml
  * zip

The skipped external-quality row is still license-review gated and is not an
active converter regression.

## Covered Baseline

The current baseline exercises:

* PDF text-flow, including two-column negative coverage and annotation-link
  rows
* unified note IR behavior across supported sources
* DOCX full notes and DOCX comments behavior
* Markdown full footnotes, including missing-body marker fallback coverage
* EPUB strong noteref full-note behavior
* Office formats: DOCX, PPTX, XLSX
* metadata sidecars and asset extraction
* ZIP/archive rows
* structured text quality signals across the external corpus

## Known Weak Coverage

These are follow-up coverage gaps, not blockers for offline PDF model work:

* HTML strong/conservative noteref external samples are still thin.
* EPUB strong-noteref external samples are still thin.
* PDF footnote body association is not implemented; PDF currently keeps the
  marker-only fallback path.
* metadata sidecar serialization for document-level `note_definitions` remains
  future work.
* OCR and runtime model integration are out of scope for this checkpoint.

## Why This Does Not Block PDF Model Work

PDF model work can return because it remains local and offline:

* converter quality is green on main samples and external-quality ready rows
* the remaining weak spots are future feature coverage, not known active
  regressions
* runtime proposal and runtime model loading stay paused
* external-quality now gives a broader regression guard for report-only model
  experiments

## Next PDF Model Scope

The next allowed PDF model scope is offline training/evaluation only:

* resume `text_block_classifier` and `layout_recovery_model` offline work
* use external-quality runs as regression guards for report-only experiments
* keep runtime wiring out of scope
* keep quality corpus rows separate from model training gold
* do not train on external-quality rows as model gold unless license and label
  roles are explicitly reviewed

## Guardrails

Corpus boundaries:

* `external_quality/` is a validation corpus.
* `DocLayNet`, `PubTables`, and model-specific corpora remain training/eval
  corpora.
* quality rows must not silently become model gold labels.

Artifact boundaries:

* do not commit `local_only/`, raw data, feature dumps, checkpoints, or local
  model outputs
* do not add a model runtime hook until the report-only quality/gate path is
  stable and separately approved
* keep runtime proposal paused until a future checkpoint explicitly reopens it
