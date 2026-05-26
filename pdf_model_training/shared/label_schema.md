# PDF Assist Model Label Schema

This schema is shared by two separate model targets:

1. `layout_recovery_model`
2. `text_block_classifier`

They do not share one flat label space.

## `text_block_classifier`

Layer:

* `convert/pdf`

Purpose:

* assist convert-layer mapping from PDF text flow to Markdown / IR block
  semantics

Primary labels:

* `paragraph`
* `heading`
* `footer_header_noise`
* `caption`
* `table_like`
* `form_row`
* `list_item`
* `separator`
* `link_text`
* `keep_as_text`
* `unknown`
* `uncertain`

Notes:

* use these labels for text-bearing block semantics
* `unknown` and `uncertain` should stay explicit when the semantic target is
  unstable
* do not reuse parser/layout labels here

## `layout_recovery_model`

Layer:

* `doc_parse/pdf/text`
* parser/layout bridge

Representative targets:

* `reading_order_risk`
* `multi_column_risk`
* `text_region`
* `heading_region`
* `table_region`
* `caption_region`
* `figure_region`
* `header_region`
* `footer_region`
* `uncertain`

Notes:

* these are parser/layout-facing recovery targets
* they should not be trained or evaluated as if they were convert-layer block
  semantics

## Legacy Compatibility Mapping

Legacy local labels can still be interpreted conservatively:

* `BodyText` -> `paragraph`
* `Heading` -> `heading`
* `Noise` -> `footer_header_noise`
* `HeaderFooter` -> `footer_header_noise`
* `PageNumber` -> `footer_header_noise`
* `Caption` -> `caption`
* `TableLike` -> `table_like`
* `CrossPageMerge` -> `layout_recovery_model` review path
* `CrossPageNoMerge` -> `layout_recovery_model` review path
* `Unknown` -> `unknown`

Important note:

* old block-only local-eval code may still collapse `Unknown` into
  `keep_as_text`; that is legacy script behavior, not the preferred schema.

## Record-Kind Guidance

* `record_kind=block` normally belongs to `text_block_classifier`
* `record_kind=boundary`, `region`, or layout-risk style rows normally belong
  to `layout_recovery_model`
* `record_kind=all` should be treated as `schema_review` until split cleanly
