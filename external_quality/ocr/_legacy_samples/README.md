# OCR Samples

This directory is reserved for real-world OCR evaluation payloads that are too
large, too source-specific, or too license-sensitive for the main repository.

Intended pipeline under evaluation:

* provider signal
* `OCRPageModel`
* layout recovery
* Markdown preview / future IR emission

Recommended structure:

* `manifest.tsv`
* `source_catalog.tsv`
* `images/`
* `expected_text/`
* `expected_markdown/`
* `provider_outputs/tesseract_tsv/`
* `provider_outputs/layout_preview/`

Policy:

* do not place PII-heavy or privacy-sensitive OCR images here
* require source, license, redistribution, and retrieval metadata before adding
  any real sample
* keep unclear-license assets out of the corpus
* this corpus is for provider signal, layout recovery, and preview evaluation;
  it does not imply current product OCR support
