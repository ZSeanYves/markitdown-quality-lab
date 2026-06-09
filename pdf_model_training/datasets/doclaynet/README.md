# DocLayNet Dataset Hub

This directory is the shared DocLayNet dataset layer for PDF model training.

It is intentionally outside individual model directories so the same source
provenance can support both:

* `layout_recovery`
* `text_block_classifier`

## Current Local State

The full local zip cache already exists at the historical text-block path:

```text
pdf_model_training/text_block_classifier/local_only/datasets/doclaynet/cache/
  DocLayNet_core.zip
  DocLayNet_extra.zip
```

That cache is local-only and must not be moved or committed as part of the
architecture scaffold.

The canonical shared path for new dataset acquisition metadata is:

```text
pdf_model_training/datasets/doclaynet/
```

The canonical shared local-only path for future raw cache/index work is:

```text
pdf_model_training/datasets/doclaynet/local_only/
```

## Ownership

Tracked here:

* dataset card and source catalog
* public provenance notes
* derived subset summaries
* local-only README files

Not tracked here:

* upstream zip files
* extracted PNG/PDF/JSON payloads
* adapted training rows
* feature matrices
* trained model parameters
* prediction dumps

## Model Use

`layout_recovery` consumes DocLayNet primarily as page/region supervision:

* title and section-header regions
* text regions
* table, picture, caption regions
* page-header and page-footer regions

`text_block_classifier` consumes DocLayNet as mapped block-level supervision:

* `heading`
* `paragraph`
* `list_item`
* `caption`
* `table_like`
* `footer_header_noise`
* reviewed `keep_as_text`

Any derived rows must preserve the upstream source label, target label, split,
adapter version, and local-only path.
