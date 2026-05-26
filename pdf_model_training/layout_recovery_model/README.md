# Layout Recovery Model

Purpose:

* assist parser/layout recovery, not convert-layer block semantics

Layer:

* `doc_parse/pdf/text`
* parser/layout bridge

Intended targets:

* reading order recovery
* multi-column risk
* region recovery
* table / figure / caption region assistance
* parser-side low-signal handling

Current status:

* planned
* checked draft manifest currently contains only a tiny migrated boundary seed
* existing boundary-style local labels are too small to represent the final
  dataset strategy

Dataset direction:

* mature public annotated layout datasets first
* keep gold and weak sources separate
* do not mix parser/layout rows with convert-layer block labels

Next action:

* define dataset intake and mapping for layout-region recovery sources
* promote only clearly parser/layout-facing manifests into this directory
* replace the tiny migrated boundary draft with mature public dataset-backed
  manifests

Do not mix:

* `paragraph`, `heading`, `caption`, `list_item`, `form_row` block semantics
  from `text_block_classifier`
* weak layout boosters into gold eval without separate reporting
