# Accurate provenance audit

This note records the source-level provenance policy for
`external_accurate/`.

Summary:

- every enrolled payload in this tree is copied from an already-reviewed source
  family under `external_quality/`
- each source subtree retains its own `_audit/PROVENANCE.md`
- accurate-only enrollment is tracked in `external_accurate/MANIFEST.tsv`
- the source/license inventory is tracked in `external_accurate/SOURCE_CATALOG.tsv`
- repo-owned accurate-only Office fixtures are retained under
  `external_accurate/repo_local/` so they are not co-mingled with the broader
  balance-quality corpus

Why a separate tree exists:

- accurate regression needs mixed evidence surfaces, not just Markdown
- OCR and PDF rows must prove provider truth and route upgrades, not merely
  non-empty text
- a dedicated tree prevents those rows from being conflated with the broader
  quality surface

Current explicit gaps:

- no public-source ODS workbook is enrolled yet for hidden-sheet / hidden-row
  accurate behavior
- no public-source PPTX file is enrolled yet that explicitly exercises a hidden
  slide

Those gaps remain visible here so that future source acquisition work can close
them without weakening the current legal/provenance bar.
