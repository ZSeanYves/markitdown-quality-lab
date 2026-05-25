# PDF Real-World Audit Report

## Current Scope

* first-round source and license audit for `pdf_corpus`
* focus on source accessibility, redistribution policy, layout-model usefulness,
  and next-round item-level candidate selection
* no runtime or converter changes
* no assertion changes
* no runtime model integration in this round
* no PDF OCR work in this round
* no bulk payload download in this round

## Accepted Source Classes

* public-domain or clearly permissive born-digital PDFs
* government forms, manuals, technical reports, and official publications with
  explicit reuse guidance
* academic or repository sources whose item-level licenses can later be filtered
* scanned archives recorded conservatively as metadata when they are useful for
  later low-signal or historical-layout research
* project-owned synthetic PDF strategies for controlled coverage gaps

## Rejected Source Classes

* large dataset mirrors without immediate row-level need
* unclear-license PDFs and mixed-provenance mirrors treated as if they were open
* PDFs with obvious `pii_risk`, signatures, financial details, or private
  records
* sources that would force this lab into a public-only gate
* scanned PDF payloads pushed into the tracked default path before a separate
  OCR or provider decision exists

## First-Round Source Snapshot

Audited source rows now in `source_catalog.tsv`: 19

Redistribution snapshot:

* `ok`: 6
* `metadata_only`: 12
* `local_only`: 0
* `forbidden`: 0
* `unknown`: 1

## P0 Source Targets

* born-digital multi-column articles with stable reading order
* manuals or specifications with heading hierarchy and numbered sections
* PDFs with figures plus captions on the same or adjacent pages
* table-heavy reports or appendices
* pages with noisy headers, footers, and page numbers
* blank forms with key-value regions
* list-heavy technical manuals

## P1 Source Targets

* cross-page paragraph continuation
* CJK or multilingual born-digital PDFs
* math-heavy or code-heavy specifications
* historical or scanned archives
* mixed-text-image or low-signal PDFs

## Initial Source Search Results

Source directions that audited well:

* IRS forms and multilingual instructions for `forms_key_value`, `cjk_pdf`,
  `heading_hierarchy`
* GAO, BLS, and NIST reports for `table_heavy`, `heading_hierarchy`,
  `footnote_header_footer`
* CDC and NIOSH manuals for `list_heavy`, `heading_hierarchy`,
  `figure_caption`
* arXiv, PMC OA, and RFC PDFs for `multi_column`, `reading_order`, `math_code`
* Chronicling America and Wikimedia Commons for `historical_scan`,
  `scanned_pdf`, `negative_low_signal`

Source directions kept conservative:

* GovInfo because the hosting platform explicitly warns that source agencies and
  embedded third-party content still matter
* NASA STI because repository items mix public-domain government works with
  contractor and third-party material
* SEC EDGAR and Federal Reserve annual reports because public access did not
  translate into a blanket tracked-payload redistribution decision in this audit
* USPTO patents because public access is clear but downstream reuse of applicant
  material is still nuanced at source level
* Internet Archive because provenance and rights vary too widely for a source
  level `ok`

## Coverage Matrix

### Document Kinds Covered by Audited Sources

* `form`
* `manual`
* `paper`
* `report`
* `book_scan`
* `newspaper`
* `annual_report`
* `table_heavy`
* `multi_column_article`
* `specification`
* `mixed_layout`

### PDF Signals Covered by Audited Sources

* `born_digital_text`
* `scanned_image_only`
* `mixed_text_image`
* `ocr_layer`
* `unknown`

### Scenario Coverage from Source Audit

* `plain_text_pdf`
* `multi_column`
* `heading_hierarchy`
* `table_heavy`
* `figure_caption`
* `footnote_header_footer`
* `forms_key_value`
* `reading_order`
* `cross_page_merge`
* `list_heavy`
* `math_code`
* `cjk_pdf`
* `historical_scan`
* `scanned_pdf`
* `mixed_text_image`
* `negative_low_signal`

### Risk Tags Reached in This Round

* `multi_column`
* `dense_text`
* `small_font`
* `heading_paragraph`
* `numbered_heading`
* `header_footer`
* `page_number`
* `footnote`
* `caption_like`
* `figure_like`
* `table_like`
* `key_value_like`
* `form_like`
* `list_like`
* `math_like`
* `code_like`
* `vertical_text`
* `cjk`
* `latin`
* `arabic`
* `multilingual`
* `cross_page_paragraph`
* `ocr_layer`
* `image_only`
* `low_signal`
* `pii_risk`
* `license_risk`
* `large_file`
* `metadata_only_candidate`

## Model Target Coverage

Covered by at least one audited source:

* `heading_vs_paragraph`
* `noise_header_footer`
* `caption_association`
* `table_region_detection`
* `reading_order_columns`
* `cross_page_merge`
* `list_continuation`
* `key_value_region`
* `low_signal_detection`

## Next-Round Item-Level Candidates

| Candidate direction | Source | Why it matters | Current policy |
| --- | --- | --- | --- |
| blank IRS form or multilingual instruction PDF | `pdf_src_0001` | safest early tracked payload for `forms_key_value` and `cjk_pdf` | `ok` |
| compact GAO report with repeated headers and appendix tables | `pdf_src_0003` | strong `noise_header_footer` plus `table_region_detection` stress | `ok` |
| NIST technical note with numbered headings, figures, and tables | `pdf_src_0004` | covers `heading_vs_paragraph` and `caption_association` together | `ok` |
| BLS handbook or report chapter with lists and tables | `pdf_src_0006` | useful `list_continuation` and `table_region_detection` baseline | `ok` |
| NIOSH safety guide or manual chapter | `pdf_src_0008` | compact public-domain manual candidate with headings and figure noise | `ok` |
| one CC BY or public-domain arXiv paper | `pdf_src_0010` | best real `multi_column` and `reading_order_columns` pressure | `metadata_only` until paper-level license check |
| one CC BY or public-domain PMC OA article | `pdf_src_0011` | good `figure_caption` and `table_heavy` candidate | `metadata_only` until article-level license check |
| one historical Chronicling America PDF page | `pdf_src_0013` | real `historical_scan` and `negative_low_signal` pressure | `metadata_only` |
| one specific Commons PDF file page with free license | `pdf_src_0014` | multilingual and historical edge cases become tractable if file rights are explicit | `metadata_only` |
| one Federal Reserve annual report section | `pdf_src_0019` | real `annual_report` and long table appendix candidate | `metadata_only` pending rights clarity |

## Conservative or Deferred Sources

| Source | Policy | Reason |
| --- | --- | --- |
| `pdf_src_0002` GovInfo | `metadata_only` | host warns that originating agencies and embedded copyrighted material still matter |
| `pdf_src_0005` NASA STI | `metadata_only` | repository mixes employee works with contractor and third-party material |
| `pdf_src_0009` SEC EDGAR | `metadata_only` | PDFs are unofficial copies and rights remain filer-specific |
| `pdf_src_0010` arXiv | `metadata_only` | every paper can carry a different license, including NC or arXiv-only terms |
| `pdf_src_0011` PMC OA | `metadata_only` | OA subset still contains multiple commercial and non-commercial license buckets |
| `pdf_src_0012` USPTO | `metadata_only` | public access is clear, but applicant-originated content makes blanket reuse awkward |
| `pdf_src_0014` Commons PDFs | `metadata_only` | file-level license and territory review still required |
| `pdf_src_0015` Internet Archive | `unknown` | provenance and rights are too mixed for source-level approval |
| `pdf_src_0017` Census publications | `metadata_only` | public-domain employee works coexist with contractor works and accepted manuscripts |
| `pdf_src_0019` Federal Reserve annual reports | `metadata_only` | public availability was clear, blanket tracked-payload reuse was not |

## Manifest Discipline

* `manifest.tsv` remains header-only in this round
* no fake `relative_path`
* no fake `sha256`
* no payload bytes were downloaded for source-catalog expansion

## Open Questions

* whether later `manifest.tsv` rows should allow metadata-only planning entries,
  or whether those should stay entirely in `audit_report.md`
* whether source-level `ok` should require a stricter item-level “third-party
  insert screened” note before any tracked payload is admitted
* whether RFC unmodified-byte redistribution is strong enough for tracked
  samples, or whether we should keep RFCs metadata-only permanently
* whether a future local helper should lint `candidate_scenarios` and
  `model_targets` note style before any payload work starts

## Next Action Checklist

* pick 3 to 5 `ok` or near-`ok` item-level PDF candidates from IRS, GAO, NIST,
  BLS, and NIOSH
* pick 2 metadata-only academic candidates from arXiv or PMC with explicit CC
  BY or public-domain notices
* keep annual reports, patents, and scanned archives conservative unless a
  specific file has unusually clear rights
* continue avoiding filled forms, signed examples, account statements, or any
  other obvious `pii_risk`
* keep PDF corpus language independent from OCR image-corpus semantics
