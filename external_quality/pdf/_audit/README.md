# PDF Corpus Audit

This directory exists only for PDF real-world quality audit and future PDF
layout-model research in `markitdown-quality-lab`.

Scope:

* this directory is for curating, auditing, and planning real-world PDF sample
  candidates
* the goal is future layout-model evaluation and integration decision support,
  not current runtime behavior
* the main repo runtime, tests, and public-only paths do not depend on this
  corpus
* current PDF runtime remains native text, asset, and metadata extraction
* runtime model integration is not part of this round
* PDF OCR is out of scope for this round
* scanned or image-only PDFs may still be cataloged for metadata and future
  provider research, but they do not enter the current default path

## What May Be Committed

Safe-to-commit files in this directory:

* `README.md`
* `source_catalog.tsv`
* `manifest.tsv`
* `manifest.example.tsv`
* `audit_report.md`
* `label_schema.md`
* `model_targets.md`
* `local_only/README.md`
* `local_only/manifest.local.example.tsv`
* compact tracked PDF payloads under a future `samples/` tree only when the
  source row is reviewed as `redistribution=ok`, the file is small, no obvious
  `pii_risk` is present, and `sha256` is recorded in `manifest.tsv`
* compact metadata-only notes that do not include payload bytes, provider
  outputs, or copied unclear-license text

Do not commit:

* large PDF mirrors or bulk dataset payloads
* PDF files whose `redistribution` is not explicitly `ok`
* any local payload under `local_only/`
* provider outputs or `.tmp` artifacts
* copied third-party license files that have not been intentionally reviewed
* PDFs containing obvious PII, signatures, addresses, phone numbers, IDs, or
  private financial content

## Corpus Boundary

This corpus is independent from the OCR image corpus:

* current shipped OCR still means main-CLI image OCR only
* this PDF corpus does not imply runtime PDF OCR support
* this PDF corpus does not imply any runtime model is active
* this PDF corpus is a research and audit surface for later real-world PDF
  evaluation
* scanned PDFs stay outside the current default path until a separate OCR or
  provider decision is made

## Taxonomy

Preferred `source_kind` values:

* `government_public`
* `public_domain_dataset`
* `permissive_dataset`
* `wikimedia_commons`
* `arxiv_or_paper`
* `annual_report`
* `manual_or_spec`
* `form_or_application`
* `academic_pdf`
* `scanned_archive`
* `synthetic`
* `restricted_dataset`
* `unknown`

Preferred `pdf_signal` values:

* `born_digital_text`
* `scanned_image_only`
* `mixed_text_image`
* `ocr_layer`
* `unknown`

Preferred `document_kind` values:

* `form`
* `manual`
* `paper`
* `report`
* `book_scan`
* `newspaper`
* `invoice_or_receipt`
* `slide_export`
* `table_heavy`
* `multi_column_article`
* `specification`
* `mixed_layout`
* `unknown`

Preferred `scenario` values:

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

Expected `risk_tags` for planning:

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
* `watermark`
* `stamp`
* `rotated_text`
* `vertical_text`
* `cjk`
* `latin`
* `arabic`
* `multilingual`
* `cross_page_paragraph`
* `two_page_spread`
* `ocr_layer`
* `image_only`
* `low_signal`
* `pii_risk`
* `license_risk`
* `large_file`
* `metadata_only_candidate`

Allowed `model_targets` values:

* `heading_vs_paragraph`
* `noise_header_footer`
* `caption_association`
* `table_region_detection`
* `reading_order_columns`
* `cross_page_merge`
* `list_continuation`
* `key_value_region`
* `low_signal_detection`
* `none`

These tags are audit and labeling hints only. They do not imply final Markdown
reconstruction quality.

## Redistribution Policy

Allowed `redistribution` values:

* `ok`: payload may be checked in after review
* `metadata_only`: keep only manifest or catalog metadata in git
* `local_only`: payload may be stored locally for audit but must stay out of
  git
* `forbidden`: do not store payload in git or a shared local corpus
* `unknown`: terms are not clear enough yet

Rules:

* default to `unknown` when license or terms are unclear
* only `ok` rows are eligible for tracked PDF payload bytes
* `metadata_only` is the default outcome for large or mixed-provenance sources
  until a tiny subset is intentionally reviewed
* `local_only` rows belong under `local_only/` and that subtree is git-ignored
* `forbidden` still allows audit notes, but not shared payload retention

## Files

Current workflow surface:

* `source_catalog.tsv`
  Source-level audit catalog for datasets, government pages, repositories,
  archives, and synthetic generation strategies.
* `manifest.tsv`
  Tracked manifest surface for reviewed PDF rows. This scaffold starts with
  field definitions only; blank fields remain blank until a real file exists.
* `manifest.example.tsv`
  Example rows showing tracked, metadata-only, and local-only usage patterns.
* `audit_report.md`
  Working summary for scope, source triage, source-search plan, and open
  questions.
* `label_schema.md`
  Future label vocabulary and review policy for layout-model research.
* `model_targets.md`
  P0 and P1 research targets and explicit out-of-scope boundaries.
* `local_only/`
  Git-ignored area for local manifests and payloads that cannot be committed.
* `.tmp/`
  Local scratch area for preview or provider experiments. Nothing under `.tmp/`
  belongs in git.

## Field Definitions

`source_catalog.tsv` fields:

* `id`
* `name`
* `source_url`
* `source_kind`
* `license`
* `redistribution`
* `candidate_scenarios`
* `notes`

`manifest.tsv` fields:

* `id`
* `relative_path`
* `source_id`
* `source_kind`
* `license`
* `redistribution`
* `local_only`
* `document_kind`
* `pdf_signal`
* `scenario`
* `risk_tags`
* `model_targets`
* `sha256`
* `notes`

Field guidance:

* `relative_path` must be repo-relative under `external_quality/pdf/` when
  present
* `relative_path` should stay blank for metadata-only planning entries that do
  not yet have commit-safe bytes
* `local_only` is `true` only for local manifests or local payload references
* `document_kind` captures the primary PDF family such as `manual` or
  `multi_column_article`
* `pdf_signal` records whether the PDF is born-digital, scanned, mixed, or has
  an OCR layer
* `scenario` uses semicolon-separated planning tags such as
  `multi_column;reading_order`
* `risk_tags` uses semicolon-separated review tags such as
  `dense_text;header_footer;metadata_only_candidate`
* `model_targets` uses semicolon-separated research targets such as
  `heading_vs_paragraph;reading_order_columns`
* `sha256` remains blank until a real local payload file exists
* `notes` should record source URL, license basis, attribution requirement when
  relevant, and any reason to keep the row conservative

## Workflow

Recommended audit flow:

1. Audit a source and record it in `source_catalog.tsv`.
2. Decide `redistribution` conservatively.
3. For large or ambiguous sources, stop at metadata-only notes first.
4. For a small, reviewed PDF that is safe to track, record a real
   `relative_path`, compute `sha256`, and add a `manifest.tsv` row.
5. Use `label_schema.md` and `model_targets.md` to decide what future labeling
   or evaluation value the sample would provide.
6. Keep scanned or image-only PDFs as metadata or later-research candidates
   unless a separate OCR or provider plan is intentionally adopted.

Example `sha256` command:

```bash
shasum -a 256 path/to/file.pdf
```

## Local-Only Policy

Use `local_only/` for:

* PDFs whose terms do not permit redistribution
* PDFs that contain obvious or unresolved PII risk
* provider outputs derived from local or non-committable files
* temporary notes that should not enter the tracked corpus

Only these two files remain tracked inside `local_only/`:

* `local_only/README.md`
* `local_only/manifest.local.example.tsv`

## What This Round Does Not Do

This scaffold does not:

* train or evaluate a production model
* change runtime extraction behavior
* add OCR fallback for scanned PDFs
* add provider-backed PDF parsing
* define public gates for main-repo CI or tests
