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

1. Build `Task A` around local-only larger datasets rather than tiny tracked
   subsets.
2. Start with `DocLayNet` as the primary gold teacher-training source.
3. Keep `PubLayNet` as a weak-layout supplement and `PubTables-1M` as a
   `table_like` specialist input.
4. Use task-aware draft manifests and adapter outputs to define teacher
   training/eval inputs.
5. Extend local-only eval later with an explicit
   `--task convert_block_classification` path.

## Mid-Term Route

1. Train stronger offline teacher models for `Task A` on larger local-only
   corpora.
2. Distill the teacher into rule suggestions, feature importance, confidence
   thresholds, and lightweight classifier candidates.
3. Add separate `Task B` local-only eval.
4. Keep Task B out of Task A label space.
5. Plan for a single provider surface that can later dispatch multiple small
   models or heads without flattening parser and convert tasks together.

## Hard Boundaries

Do not do the following:

* do not train or ship a runtime model by default
* do not make the CLI depend on a heavy teacher model
* do not use this track as a PDF OCR path
* do not treat model output as a replacement for deterministic rules
* do not mix parser boundary labels and convert block labels into one flat
  classifier

## Teacher / Distillation Boundary

The intended split is:

* teacher training may be heavy, local-only, and dataset-rich;
* runtime candidates, if any, must be small and optional;
* teacher outputs are for offline analysis and distillation, not direct CLI
  dependency;
* weak-label sources must never be treated as gold evaluation for Task A.

## Fail-Closed Rule

If this track is ever connected to runtime behavior:

* deterministic rules remain primary
* model support must be optional and explainable
* the system must fail closed when the model is absent, disabled, weak, or
  out of scope
