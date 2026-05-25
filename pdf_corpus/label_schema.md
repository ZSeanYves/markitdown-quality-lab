# PDF Label Schema Draft

This file defines what later layout-model research may label. It does not mean
that annotation is required in this round.

## Label Layers

### Block-Level Labels

Candidate block labels:

* `heading`
* `paragraph`
* `list_item`
* `table_region`
* `table_caption`
* `figure_region`
* `figure_caption`
* `key_value_region`
* `header`
* `footer`
* `page_number`
* `footnote`
* `noise`

Block-level expectations:

* labels should describe layout role, not semantic truth claims
* labels may be attached to a bounding region, reading-order segment, or
  extracted block candidate depending on later tooling
* uncertain blocks should be marked for review rather than forced into a wrong
  class

### Page-Level Labels

Candidate page labels:

* `plain_text_page`
* `multi_column_page`
* `table_heavy_page`
* `form_page`
* `mixed_text_image_page`
* `historical_scan_page`
* `low_signal_page`

Page-level labels help with:

* source triage
* sampling balance
* routing to likely `model_targets`

### Reading-Order Labels

Candidate reading-order labels:

* `column_1_before_column_2`
* `caption_after_figure`
* `footnote_after_body`
* `header_footer_noise`
* `cross_page_continuation`
* `list_continuation`

These labels should remain lightweight and auditable. They are intended to
measure ordering risk, not full semantic understanding.

## Noise and Structural Labels

Noise or low-value layout labels:

* `header`
* `footer`
* `page_number`
* `watermark`
* `stamp`
* `rotated_text`
* `low_signal`

Structural disambiguation labels:

* `caption_like`
* `table_like`
* `key_value_like`
* `figure_like`

These are label categories for review and model research only. They are not a
guarantee of final Markdown reconstruction behavior.

## Model-Target Mapping

Suggested label-to-target mapping:

* `heading` vs `paragraph` -> `heading_vs_paragraph`
* `header`, `footer`, `page_number`, `noise` -> `noise_header_footer`
* `figure_caption`, `table_caption`, `figure_region` -> `caption_association`
* `table_region` -> `table_region_detection`
* `column_1_before_column_2` -> `reading_order_columns`
* `cross_page_continuation` -> `cross_page_merge`
* `list_item`, `list_continuation` -> `list_continuation`
* `key_value_region`, `form_page` -> `key_value_region`
* `low_signal`, `historical_scan_page`, `mixed_text_image_page` ->
  `low_signal_detection`

## Confidence and Review Policy

When later labeling starts, each label may carry one of:

* `high`
* `medium`
* `low`
* `uncertain`

Guidance:

* `uncertain` means the row should enter a review bucket
* low-confidence labels should not silently become training truth
* ambiguous blocks should preserve notes about why they are hard

## Review Bucket

Rows should enter a review bucket when:

* layout role is ambiguous between two classes
* OCR-layer presence is unclear
* figure-caption association spans page boundaries
* headers or footnotes are inconsistent across pages
* license, privacy, or provenance concerns remain partially unresolved

Review buckets are expected to slow down sample admission on purpose. Conserving
audit quality matters more than row count.
