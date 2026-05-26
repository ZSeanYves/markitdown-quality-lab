# PDF Text-Flow Assist Label Schema

This directory contains local-only schema and label assets for the PDF
text-flow assist model track.

The schema is task-aware and layer-aware. Boundary labels do not belong in the
same flat classifier as convert-layer block labels.

## Task A: convert_block_classification

Layer: `convert/pdf`

Purpose:

* assist convert-layer mapping from PDF line/block text flow to Markdown / IR
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

* these labels are for convert-layer semantic assistance only
* boundary labels do not belong in this task
* `unknown` or `uncertain` should stay explicit when the intent is not stable
  enough for a stronger semantic class

## Task B: parser_boundary_assist

Layer: `doc_parse/pdf/text` or parser/layout bridge

Purpose:

* assist parser-layer decisions around cross-page boundaries, low-signal
  transitions, and reading-order risk

Primary labels:

* `cross_page_merge`
* `cross_page_no_merge`
* `low_signal`
* `usable_text`
* `multi_column_risk`
* `uncertain`

Notes:

* these labels are not part of Task A convert-layer block classification
* they should be trained and evaluated separately from block labels

## Task C: parser_layout_signal_assist

Layer: parser/layout feature

Purpose:

* future-only parser/layout signal assistance for cases such as `low_signal`,
  `image_only`, `scanned_ish`, `reading_order_risk`, or stronger
  multi-column-risk detection

Notes:

* Task C is a future target only
* it is not part of the current training mainline

## Legacy Compatibility Mapping

Legacy local labels can still be interpreted with the following mapping guide:

* `BodyText` -> `paragraph`
* `Heading` -> `heading`
* `Noise` -> `footer_header_noise`
* `HeaderFooter` -> `footer_header_noise`
* `PageNumber` -> `footer_header_noise`
* `Caption` -> `caption`
* `TableLike` -> `table_like`
* `CrossPageMerge` -> `cross_page_merge`
* `CrossPageNoMerge` -> `cross_page_no_merge`
* `Unknown` -> `unknown`

Important note:

* older local eval code may still collapse `Unknown` into a more specific
  fallback such as `keep_as_text`; that is legacy local-eval behavior, not the
  preferred schema meaning going forward

## Record-Kind Guidance

* `record_kind=block` should normally map to `Task A`
* `record_kind=boundary` should normally map to `Task B`
* `record_kind=all` should not remain ambiguous

If a row or file mixes convert-task and parser-task semantics under
`record_kind=all`, the preferred action is:

* split it into task-specific rows or files, or
* mark it `schema_review` until the target is unambiguous

## Current Scope Notes

* this lab remains local-only and research-only
* current held-out checks are small-sample sanity checks, not generalized
  quality claims
* Task A currently has materially more labeled coverage than Task B
* Task B currently has only a tiny local seed set and should stay separate
