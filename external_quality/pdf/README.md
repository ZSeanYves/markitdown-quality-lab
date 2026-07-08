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
- accurate-only scanned-PDF OCR rows now live under
  `external_accurate/repo_local/pdf/ocr/`, so this tree stays focused on
  broader PDF quality and native-reader coverage
- broader repo-owned PDF expected outputs, OCR fixtures, and RAG payloads live
  under `external_main_process/pdf/`, not in this external-quality subtree

Local audit notes:

- `irs/_audit/PROVENANCE.md` closes the per-file provenance note for retained
  IRS PDF samples
- `niosh/_audit/PROVENANCE.md` records the public-domain statement retained for
  the promoted NIOSH PDFs
- `nist/_audit/PROVENANCE.md` records the NIST technical-series licensing
  anchor used for retained NIST samples

Current promoted source highlights:

- `pdf/qpdf/` now includes compact Apache-2.0 qpdf fixtures for hybrid xref
  traversal and object-stream-backed text recovery, complementing the existing
  internal-destination and outline samples with coverage that is directly
  relevant to the native reader's xref-driven path.
