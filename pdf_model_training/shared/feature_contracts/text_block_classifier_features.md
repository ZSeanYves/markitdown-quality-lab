# text_block_classifier Feature Contract

Layer:

* PDF convert layer

Consumer:

* convert-owned IR and Markdown decisions

## Inputs

Expected feature families:

* parser-produced block, line, span, and page geometry
* block text and token statistics
* font, size, indentation, and line gap signals when available
* page index and page-position buckets
* neighboring block context
* nearby table, figure, annotation, and image hints
* optional parser-owned `layout_recovery` soft hints

## Outputs

Allowed output families:

* block semantic role labels
* soft hints and confidence scores
* abstain or low-confidence flags

Primary labels:

* `heading`
* `paragraph`
* `caption`
* `table_like`
* `list_item`
* `footer_header_noise`
* `form_row`
* `link_text`
* `keep_as_text`
* `code_like`
* `footnote_like`
* `page_number_noise`
* `separator`
* `uncertain`

## Runtime Boundary

The convert layer may use parser-owned layout signals as features. It must not
rewrite parser canonical layout or feed its semantic labels back into parser
layout recovery.

Heavy teacher checkpoints, generated features, prediction dumps, and local eval
reports remain external-only.
