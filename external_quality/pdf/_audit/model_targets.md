# PDF Model Targets

This file defines the future layout-model targets that the PDF corpus is meant
to support. It does not imply any current runtime integration.

## P0 Targets

### `heading_vs_paragraph`

Goal:

* separate section titles, numbered headings, and normal paragraph blocks

Useful source patterns:

* manuals
* standards
* reports
* technical papers with explicit heading hierarchy

### `noise_header_footer`

Goal:

* suppress or isolate repeated headers, footers, and page-number noise

Useful source patterns:

* formal reports
* slide exports with repeating banners
* manuals with running headers

### `caption_association`

Goal:

* distinguish figure or table captions from adjacent body text

Useful source patterns:

* academic papers
* reports with figures and tables
* manuals with inline diagrams

### `table_region_detection`

Goal:

* identify table regions reliably enough for later extraction-policy decisions

Useful source patterns:

* reports with appendix tables
* specifications with matrix-like sections
* financial or operational tables without private content

### `reading_order_columns`

Goal:

* recover column order and avoid cross-column merge errors

Useful source patterns:

* multi-column articles
* conference papers
* newspapers with clear column structure

## P1 Targets

### `cross_page_merge`

Goal:

* detect when a paragraph or section continues across page boundaries

### `list_continuation`

Goal:

* preserve ordered or unordered list continuity across blocks and pages

### `key_value_region`

Goal:

* identify blank forms, application fields, and key-value regions without
  turning this corpus into OCR-form understanding work

### `low_signal_detection`

Goal:

* recognize when a page is too noisy, scanned, image-heavy, or otherwise weak
  for the default text-first path

## Explicitly Out Of Scope This Round

This scaffold does not do:

* OCR text recognition
* PDF OCR providers
* scanned PDF fallback
* semantic understanding
* LLM-based interpretation
* runtime model integration
