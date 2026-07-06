# PDF External Quality

This subtree contains PDF-related external quality material.
It is the PDF-specific branch of the formal `external_quality/` corpus surface.

Subtrees:

- `_audit/`: PDF real-world audit scaffold, source notes, and promotion support
- `irs/`, `nist/`, `niosh/`: tracked PDF samples grouped by audited public
  source family
- `pdfbox/`, `pdfjs/`, `qpdf/`, `markitdown/`, `markitdown-repo/`: source-grouped
  fixture payloads used by formal quality rows
- `archive/`: migration-only or legacy layout notes and payload history

Boundary:

- this tree is for corpus quality work, not runtime integration
- promoted formal rows must still be anchored by
  `external_quality/MANIFEST.tsv` and `external_quality/SOURCE_CATALOG.tsv`
- small runtime-facing PDF OCR gate rows are allowed here when they are
  OCR-suitable, traceable, and kept separate from broader native-text PDF
  intake
- the current shipped PDF OCR gate is intentionally narrow: explicit
  scanned-PDF OCR rows that exercise OCR-only behavior, not future
  layout-model recovery
- layout-model training assets do not live here; they belong in
  `pdf_model_training/`

Local audit notes:

- `irs/_audit/PROVENANCE.md` closes the per-file provenance note for retained
  IRS PDF samples
- `niosh/_audit/PROVENANCE.md` records the public-domain statement retained for
  the promoted NIOSH PDFs
- `nist/_audit/PROVENANCE.md` records the NIST technical-series licensing
  anchor used for retained NIST samples
