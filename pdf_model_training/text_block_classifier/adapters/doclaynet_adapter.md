# DocLayNet -> Text Block Classifier Adapter

## Purpose

This adapter prepares local-only `DocLayNet` annotations for
`text_block_classifier`.

It is not a training entrypoint and it does not modify any active manifest.

## Why This Adapter Lives Here

`DocLayNet` is currently the best public gold source for convert-layer block
labels. This adapter is intentionally scoped to:

* `model_target=text_block_classifier`
* `layer=convert/pdf`

It does not define parser/layout recovery labels.

## Inputs

Preferred inputs:

1. DocLayNet COCO annotations
2. DocLayNet extra JSON text cells
3. optional page metadata

The adapter never downloads data. It only consumes local files already present
on disk.

## Output

Recommended TSV fields:

* `sample_id`
* `source_dataset`
* `source_page_id`
* `source_region_id`
* `page_no`
* `bbox`
* `source_label`
* `target_label`
* `target_task`
* `text`
* `confidence`
* `split`
* `notes`

`target_task` remains `convert_block_classification` for compatibility with the
existing Task A naming, but the owning directory is now `text_block_classifier`.

## Mapping Rules

Direct positive mappings:

* `Title` -> `heading`
* `Section-header` -> `heading`
* `Text` -> `paragraph`
* `List-item` -> `list_item`
* `Caption` -> `caption`
* `Page-header` -> `footer_header_noise`
* `Page-footer` -> `footer_header_noise`
* `Table` -> `table_like`

Restricted or review mappings:

* `Footnote` -> `keep_as_text`
* `Formula` -> `uncertain`
* `Picture` -> `uncertain`

Do not flatten `Formula` or `Picture` into `paragraph`.

## Text Recovery

Preferred strategy:

1. load page JSON text cells
2. match cells to regions by bbox overlap
3. concatenate matched text

If text cells are missing:

* keep the row
* leave `text` empty
* write a `missing_text_cells` note

## Why This Does Not Enter Checked Training Directly

Do not promote raw adapter output straight into a checked training manifest
because:

* larger DocLayNet payloads should remain local-only
* gold/weak split policy still needs to stay explicit
* review-only source labels such as `Footnote`, `Formula`, and `Picture` need
  controlled export policy

Use this adapter to create local-only exports first. Promote only reviewed
drafts later.
