# Layout Recovery Model Label Schema

Layer:

* `doc_parse/pdf/text`
* parser/layout bridge

Purpose:

* assist layout recovery, reading-order recovery, and parser-side region
  interpretation

Representative labels:

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

Notes:

* this schema is parser/layout-facing, not convert-layer block semantics
* old repo-manual boundary labels under `archive/repo_manual_labels/` are only
  tiny historical reference rows
* keep region recovery and text-block classification in separate manifests and
  reports
