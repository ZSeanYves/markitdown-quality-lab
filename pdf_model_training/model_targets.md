# PDF Text-Flow Assist Model Targets

## Overall Goal

The PDF text-flow assist model is a rule-supporting model family for the PDF
pipeline.

It does not replace the checked deterministic rule system. Any future runtime
use must stay behind explicit rule gates and fail closed when model support is
missing, weak, or intentionally disabled.

## Task A: convert_block_classification

Layer: `convert/pdf`

Purpose:

* assist convert-layer mapping from PDF line/block text flow to Markdown / IR
  semantics

Examples of target labels:

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

Recommended model target name:

* `convert_block_classifier`

## Task B: parser_boundary_assist

Layer: `doc_parse/pdf/text`

Bridge surface:

* parser/layout bridge

Purpose:

* assist parser-layer decisions around cross-page boundaries, low-signal
  transitions, and reading-order risk

Examples of target labels:

* `cross_page_merge`
* `cross_page_no_merge`
* `low_signal`
* `usable_text`
* `multi_column_risk`
* `uncertain`

Recommended model target name:

* `parser_boundary_assist`

## Task C: parser_layout_signal_assist

Layer: parser/layout feature

Purpose:

* future-only layout-signal assistance for `low_signal`, `image_only`,
  `scanned_ish`, `reading_order_risk`, and stronger multi-column risk cases

Recommended model target name:

* `parser_layout_signal_assist`

Status:

* future target only
* not part of the current training mainline

## Near-Term Route

1. Start with `Task A` smoke only.
2. Use `manifest.v2.tsv` style drafts to bring more block labels under a
   task-aware schema.
3. Extend local-only eval later with an explicit
   `--task convert_block_classification` path.

## Mid-Term Route

1. Add separate `Task B` local-only eval.
2. Keep Task B out of Task A label space.
3. Plan for a single provider surface that can later dispatch multiple small
   models or heads without flattening parser and convert tasks together.

## Hard Boundaries

Do not do the following:

* do not train or ship a runtime model by default
* do not use this track as a PDF OCR path
* do not treat model output as a replacement for deterministic rules
* do not mix parser boundary labels and convert block labels into one flat
  classifier

## Fail-Closed Rule

If this track is ever connected to runtime behavior:

* deterministic rules remain primary
* model support must be optional and explainable
* the system must fail closed when the model is absent, disabled, weak, or
  out of scope
