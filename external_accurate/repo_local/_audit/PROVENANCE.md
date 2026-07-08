Repo-local Office accurate audit note

Sample group: `external_accurate/repo_local`

Reviewed files:
- `docx/docx_textbox_basic.docx`
- `pdf/ocr/pdf_ocr_single_page.pdf`
- `pdf/ocr/pdf_ocr_two_page.pdf`
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
- Retain the repo-owned scanned-PDF OCR fixtures only in the dedicated
  accurate tree so single-page and multi-page PDF OCR route coverage no longer
  lives on the general `external_quality/` surface.
