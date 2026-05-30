# Layout Recovery Model Data Readiness

Date: 2026-05-31

## Decision

Training readiness: `not_ready`.

`layout_recovery_model` should not be trained or connected to runtime yet. The
current tree has a clean Task B ownership boundary, but it does not yet have a
mature independent gold corpus for parser/layout recovery.

## Task B Scope

Task B is parser/layout recovery, not convert-layer block semantics.

In scope:

* reading order
* paragraph boundary
* column boundary
* cross-page merge/split
* attachment relation
* footnote body association as future parser/layout work

Representative model labels remain parser/layout-facing:

* `reading_order`
* `column_region`
* `table_region`
* `figure_region`
* `caption_region`
* `header_footer_region`
* `cross_page_merge`
* `cross_page_no_merge`
* `multi_column_risk`
* `uncertain`

Out of scope:

* final Markdown block semantics such as `paragraph`, `heading`,
  `list_item`, `caption`, `table_like`, or `keep_as_text`
* text block classifier distillation hints
* convert-layer runtime override policy

## Current Data Inventory

| source | status | use | readiness |
| --- | --- | --- | --- |
| `layout_recovery_model/manifests/manifest.tsv` | header-only | active manifest entrypoint | not trainable |
| main-repo `debug/testdata/layout_assist_eval/boundary_assist_manifest.tsv` | one manual boundary sample | debug smoke for cross-page merge | unsuitable as model gold |
| `archive/repo_manual_labels/*` | tiny historical rows | reference only | unsuitable as active manifest |
| main-repo PDF merge tests | deterministic guard coverage | regression tests for current rules | not model training data |
| external-quality PDF samples | validation/report-only signals | runtime-quality regression guard | not training gold without review |
| DocLayNet | human layout-region annotations | preferred first gold region baseline | suitable after adapter and split design |
| PubLayNet | weak layout-region annotations | weak booster only | suitable only as separated weak data |
| PubTables-1M | table detection/structure data | table-region specialist | not a full Task B corpus |

Current tracked dataset metadata says:

* `DocLayNet` is the priority public gold source with high layout mapping
  quality.
* `PubLayNet` can be a weak layout booster, but should stay separate from gold
  evaluation.
* `PubTables-1M` is useful for table-region specialization, not full layout
  recovery.
* The current active manifest is intentionally header-only until mature public
  dataset adapters are defined.

## Why Training Is Not Ready

Training is blocked because:

* there is no active gold manifest with enough Task B examples
* the only split Task B debug manifest has one heldout cross-page merge row
* archived repo-manual boundary rows are tiny historical references, not a
  dataset
* existing main-repo tests cover deterministic rule behavior, not model
  generalization
* external-quality rows have not been reviewed and must not be promoted to
  training gold
* DocLayNet/PubLayNet/PubTables adapters and source-separated eval splits still
  need to be built

## Acquisition Plan

Initial gold lane:

* source: `DocLayNet`
* labels available: layout regions such as title, section header, table,
  caption, picture, page header, and page footer
* expected adapter: `page_region_adapter`
* expected mapping: `doclaynet_to_layout_recovery_labels`
* size target: start with a smoke slice of about 100 pages, then a pilot slice
  of about 1,000 pages, then a larger train/dev/heldout slice after the adapter
  is stable
* license: CDLA-Permissive-1.0
* split/eval strategy: source-separated train/dev/heldout; keep document/page
  groups from leaking across splits; report per-region metrics and focused
  boundary-risk slices separately

Weak booster lane:

* source: `PubLayNet`
* labels available: COCO-style layout boxes and released page/PDF material
* expected adapter: `coco_region_adapter`
* expected mapping: `publaynet_to_layout_recovery_labels`
* size target: small weak smoke slice first, then a larger weak-only supplement
* license: CDLA-Permissive-1.0 with official item-page reconfirmation before
  any wider use
* split/eval strategy: never mix weak data into gold eval; report weak-only
  training influence separately

Table specialist lane:

* source: `PubTables-1M`
* labels available: table detection/structure annotations and table/page
  crops
* expected adapter: `table_region_adapter`
* expected mapping: `pubtables_to_table_region`
* size target: smoke slice for table-region detection, then table-focused pilot
* license: needs review before use beyond metadata planning
* split/eval strategy: table-only specialist eval; do not claim full layout
  recovery coverage from table-only results

Boundary extension lane:

* source: reviewed project PDFs or future public datasets with explicit
  reading-order and cross-page boundary annotations
* labels available: cross-page merge/split, paragraph boundary, column
  boundary, attachment relation, and future footnote body association
* expected adapter: a boundary-pair adapter that emits parser/layout transition
  examples, not block-semantic labels
* size target: at least hundreds of reviewed boundary pairs before any model
  experiment; thousands before runtime discussion
* license: must be explicit for every source, with local-only bytes kept out of
  the tracked repo
* split/eval strategy: document-grouped splits; keep cross-page, multi-column,
  table-adjacent, and footnote-adjacent slices visible as separate eval buckets

## Do-Not-Cross Boundaries

Do not mix Task A text-block semantics with Task B parser/layout recovery.

Do not train `layout_recovery_model` from unreviewed external-quality rows.

Do not treat product tests, debug smoke manifests, or archived repo-manual rows
as mature model gold.

Do not connect runtime integration, default hooks, or converter behavior to this
readiness document.

Do not commit local-only dataset bytes, generated features, model checkpoints,
prediction dumps, or evaluation reports.
