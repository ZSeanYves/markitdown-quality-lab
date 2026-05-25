# PDF External Quality

This subtree contains PDF-related external quality material.

Subtrees:

* `_audit/`: PDF real-world audit scaffold, source catalog, and seed manifest
* `irs/`, `nist/`, `niosh/`: tracked PDF audit seed samples grouped by source
* `pdfbox/`, `pdfjs/`, `qpdf/`, `markitdown/`, `markitdown-repo/`: source-grouped fixture payloads used by quality rows
* `archive/`: migration-only or legacy layout notes and payload history

Boundary:

* this tree is for corpus quality work, not runtime integration
* PDF OCR is still out of scope here
* layout-model training assets do not live here; they belong in `pdf_model_training/`
