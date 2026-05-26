# PDF Model Training

This directory contains offline-only research assets for two PDF assist-model
targets:

1. `layout_recovery_model`
2. `text_block_classifier`

The training track exists to support rule-based PDF parsing and conversion, not
to replace them. Training may be heavy and local-only. Any future runtime
candidate must stay lightweight, rule-gated, and fail closed.

## Directory Layout

* `shared/`
  Shared schema, dataset registry, source catalog, and policy documents.
* `layout_recovery_model/`
  Parser/layout-facing planning, manifests, adapters, scripts, and future
  evaluation/model slots for reading order, column risk, and layout-region
  recovery.
* `text_block_classifier/`
  Convert-layer planning, manifests, adapters, scripts, and historical model
  assets for block labels such as paragraph, heading, footer/header noise,
  caption, table-like, form-row, list-item, separator, link-text, and
  keep-as-text.
* `datasets/`
  Tracked tiny metadata, public sample references, and existing small fixture
  assets. Full public datasets do not belong here.
* `labels/`
  Existing local label TSVs. This round does not rewrite label contents.
* `local_only/`
  Git-ignored home for larger local datasets, teacher artifacts, feature dumps,
  and local manifests.
* `archive/`
  Legacy manifests, superseded planning material, and migration notes.
* `scripts/`
  Shared helper scripts that are still genuinely cross-target.

## Model Boundaries

### `layout_recovery_model`

Layer:

* `doc_parse/pdf/text`
* parser/layout bridge

Focus:

* reading order recovery
* multi-column risk
* layout regions
* table / figure / caption region assistance
* parser-side boundary and recovery signals

### `text_block_classifier`

Layer:

* `convert/pdf`

Focus:

* paragraph vs heading
* footer/header noise
* caption
* table-like
* form-row
* list-item
* separator
* link-text
* keep-as-text

Do not flatten these two targets into one classifier or one mixed manifest.

## Dataset Direction

The preferred training sources are mature public annotated datasets:

* `DocLayNet` as the primary gold source
* `PubLayNet` as a weak-layout supplement
* `PubTables-1M` as a table specialist

Small tracked subsets are only for adapter and schema sanity. Meaningful
teacher training belongs in `local_only/` and must not be committed.

## Historical Notes

Older root-level manifests, planning TSVs, and one-off policy documents were
migrated into `shared/`, `text_block_classifier/`, or `archive/` during this
cleanup. Historical model JSON files remain as legacy artifacts under
`text_block_classifier/models/`; they do not imply a current recommended
runtime model.
