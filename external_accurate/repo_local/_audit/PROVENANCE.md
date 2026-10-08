Repo-local Office accurate audit note

Sample group: `external_accurate/repo_local`

Reviewed files:
- `docx/docx_textbox_basic.docx`
- `xlsx/xlsx_hidden_sheets_policy.xlsx`
- `pptx/pptx_callout_blocks_basic.pptx`
- `LICENSE-markitdown-repo-local.txt`

Evidence retained locally:
- Source group:
  `https://github.com/ZSeanYves/markitdown/tree/main/external_accurate/repo_local`
- Local Apache-2.0 license mirror: `LICENSE-markitdown-repo-local.txt`
- The originating repo-owned source-group conclusion was previously tracked in
  `external_quality/SOURCE_CATALOG.tsv` under `markitdown_repo_office_samples`

Review conclusion:
- Retain these repo-owned Office fixtures only in the dedicated accurate tree
  so textbox anchoring, hidden-sheet materialization, and PPTX reading-order
  recovery are covered without leaving accurate-tagged rows in
  `external_quality/`.
- Scanned-PDF OCR fixtures were retired with the 0.8 text-only contract. The
  accurate tree now keeps only Office fixtures and born-digital PDF provenance
  rows.
