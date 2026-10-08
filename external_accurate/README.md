# External Accurate

This tree is the dedicated external accurate-regression surface for
`markitdown`.

It mirrors the contract shape of `external_quality/`, but it is intentionally
separate:

- `external_quality/` tracks broader quality signals across the default product
  surface
- `external_accurate/` tracks accurate-only behavior, route upgrades, provider
  truth, and feature-specific output differences

Structure rules:

- organize first by format, then by source
- keep tracked payloads under `external_accurate/<format>/<source>/...`
- keep one `_audit/PROVENANCE.md` per source subtree
- keep the machine-readable contract in `MANIFEST.tsv`
- keep the source/license index in `SOURCE_CATALOG.tsv`

Validation surfaces:

- `markdown`
  use when accurate mode has a stable visible output difference
- `debug`
  use when accurate evidence lives in route metrics, provider facts, or applied
  feature diagnostics
- `provenance`
  use when the stable contract is the conversion sidecar rather than the user
  markdown

Current enrolled formats:

- `docx/`
- `xlsx/`
- `pptx/`
- `odt/`
- `ods/`
- `odp/`
- `pdf/`

Current source families:

- audited upstream fixture families such as Open XML SDK, Apache POI,
  XlsxWriter, python-pptx, and ODF Toolkit
- repo-owned Office fixtures under `external_accurate/repo_local/` for
  accurate-only coverage that should not remain in `external_quality/`
- born-digital PDF fixtures under `external_accurate/pdf/` for accurate text
  layer and provenance coverage

Current known curated gaps:

- no public-source ODS sample is enrolled yet for `ods_hidden_sheets` or
  `ods_hidden_rows`
- no public-source PPTX sample is enrolled yet that explicitly exercises
  hidden-slide semantics
- OCR and scanned-page provider rows are retired. Accurate PDF rows must use
  the shared text-layer route and may assert `page_single_pass` provenance.

These gaps are explicit on purpose. The accurate suite should only enroll
samples with a complete redistribution and provenance chain.
