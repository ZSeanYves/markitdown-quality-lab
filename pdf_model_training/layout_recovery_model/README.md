# Layout Recovery Model

Purpose:

* assist parser/layout recovery, not convert-layer block semantics

Layer:

* `doc_parse/pdf/text`
* parser/layout bridge

Representative targets:

* `reading_order`
* `column_region`
* `table_region`
* `figure_region`
* `caption_region`
* `header_footer_region`
* `cross_page_merge`
* `cross_page_no_merge`
* `low_signal`
* `usable_text`
* `multi_column_risk`
* `uncertain`

Dataset sources:

* `DocLayNet` region annotations
* `PubLayNet` weak layout regions
* `PubTables-1M` table-region specialist data

Current status:

* this directory now owns a full per-model training layout:
  `dataset/`, `adapters/`, `labels/`, `manifests/`, `training/`,
  `evaluation/`, `models/`, `reports/`, `scripts/`, `local_only/`, `archive/`
* `manifests/manifest.tsv` is the only current recommended manifest entrypoint
* the current active manifest is intentionally header-only until mature public
  dataset adapters are defined
* old repo-manual boundary rows have been moved into
  `archive/old_manifests/` and `archive/repo_manual_labels/`

Next action:

* define adapter outputs from mature public layout-region datasets
* keep gold and weak layout sources separate
* keep parser/layout recovery distinct from text block semantics

Do not mix:

* `paragraph`, `heading`, `caption`, `list_item`, `form_row` block semantics
  from `text_block_classifier`
* old repo-manual boundary rows into the current recommended manifest
