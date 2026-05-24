# OCR Corpus Audit

This directory exists only for OCR real-world quality audit work in
`markitdown-quality-lab`.

Scope:

* this directory is for curating, auditing, and planning real-world OCR sample
  candidates
* the goal is coverage work for the shipped main-CLI image OCR path
* PDF OCR is out of scope for this round, but rendered page-image candidates may
  still be cataloged for future manual review
* this directory does not define a product gate or a public-only gate
* this directory does not change runtime, converter behavior, OCR assertions, or
  current fail-closed PDF OCR boundaries

Current OCR boundary:

* shipped OCR currently means image OCR on the main CLI
* image OCR depends on local `tesseract` plus matching language data
* this audit directory is for source/license/risk review plus future sample
  planning
* PDF OCR remains fail-closed and is not part of this corpus round

## What May Be Committed

Safe-to-commit files in this directory:

* `README.md`
* `source_catalog.tsv`
* `manifest.tsv`
* `manifest.example.tsv`
* `audit_report.md`
* `local_only/README.md`
* `local_only/manifest.local.example.tsv`
* compact tracked sample files under `samples/` whose source row is reviewed as
  `redistribution=ok` and whose `sha256` is recorded in `manifest.tsv`
* compact metadata-only notes that do not include payload bytes, provider
  outputs, or copied unclear-license text

Do not commit:

* real sample files whose `redistribution` is not explicitly `ok`
* any local payload under `local_only/`
* provider outputs generated from local-only or non-committable inputs
* copied third-party license files that have not been intentionally reviewed
* PII-heavy files, raw receipts, addresses, phone numbers, signatures, IDs, or
  large dataset mirrors

## Taxonomy

Level-1 `scenario` values:

* `plain_print`
* `layout`
* `structured`
* `degradation`
* `language`
* `negative`
* `scene_text`
* `handwriting`
* `historical`
* `synthetic`
* `pdf_page_image`

Level-2 `risk_tags` currently expected in audit planning:

* `clean_print`
* `small_font`
* `dense_text`
* `multi_column`
* `mixed_reading_order`
* `heading_paragraph`
* `caption_like`
* `table_like`
* `key_value_like`
* `form_like`
* `receipt_like`
* `invoice_like`
* `ticket_like`
* `menu_like`
* `label_like`
* `signage_like`
* `chart_with_text`
* `code_like`
* `math_like`
* `footnote_like`
* `header_footer`
* `page_number`
* `watermark`
* `stamp`
* `signature`
* `logo_noise`
* `low_resolution`
* `blur`
* `skew`
* `perspective`
* `shadow`
* `compression_artifact`
* `background_texture`
* `low_contrast`
* `cjk`
* `latin`
* `arabic`
* `devanagari`
* `multilingual`
* `digits_amounts_units`
* `vertical_text`
* `handwritten`
* `historical_scan`
* `typewriter`
* `no_text`
* `text_too_sparse`
* `pii_risk`
* `license_risk`
* `large_dataset`
* `download_required`
* `metadata_only_candidate`

These labels are audit tags only. Semantic labels such as `TableLike`,
`KeyValueLike`, and `CaptionLike` remain observational hints and must not be
read as a Markdown reconstruction promise.

## Source Kinds

Preferred `source_kind` values:

* `self_synthetic`
* `public_domain_dataset`
* `permissive_dataset`
* `restricted_dataset`
* `government_public`
* `wikimedia_commons`
* `kaggle_dataset`
* `huggingface_dataset`
* `github_dataset`
* `paper_dataset`
* `commercial_dataset`
* `web_page`
* `unknown`

## Redistribution Policy

Allowed `redistribution` values:

* `ok`: payload may be checked in after review
* `metadata_only`: keep only manifest/catalog metadata in git
* `local_only`: payload may be stored locally for audit but must stay out of git
* `forbidden`: do not store payload in git or a shared local corpus; keep only
  audit notes
* `unknown`: terms are not clear enough yet

Rules:

* default to `unknown` when license or terms are unclear
* only `ok` is eligible for tracked payload bytes
* `metadata_only` is the default outcome for large or mixed-provenance public
  sources until we intentionally review a small subset
* `local_only` rows belong under `local_only/` and that subtree is git-ignored
* `forbidden` means the source may still be cataloged, but not downloaded into a
  shared tracked corpus

## Files

* `source_catalog.tsv`
  Source-level audit catalog for public datasets, official pages, repositories,
  government archives, and synthetic generation strategies.
* `manifest.tsv`
  Candidate-row planning surface. It may contain metadata-only rows with blank
  `relative_path` and blank `sha256` when the source has been audited but no
  local file has been staged yet.
* `samples/`
  Checked-in seed sample tree for small `redistribution=ok` OCR payloads grouped
  by scenario.
* `manifest.example.tsv`
  Example row template showing recommended field usage.
* `audit_report.md`
  Working audit summary: source triage, scenario coverage, candidate row plans,
  and open questions.
* `local_only/`
  Git-ignored area for local manifests and payloads that cannot be committed.

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
* `language_hint`
* `scenario`
* `risk_tags`
* `expected_preview`
* `expected_hints`
* `sha256`
* `notes`

Field guidance:

* `relative_path` must be repo-relative under `ocr_corpus/` when present
* `relative_path` may be blank only for tracked metadata-only planning rows
* `local_only` is `true` only for local manifests or local payload references
* `scenario` uses level-1 tags such as `layout;structured`
* `risk_tags` uses level-2 tags such as
  `multi_column;dense_text;metadata_only_candidate`
* `expected_preview` is a compact review expectation, not a golden assertion
* `expected_hints` is a compact review expectation for future hint inspection,
  not a product contract
* `sha256` should remain blank until a real local payload file exists

## Online Source Audit Workflow

For each online source:

1. Verify the source is still reachable.
2. Find the clearest available license or terms page.
3. Record whether commercial use appears allowed.
4. Record whether derivative use appears allowed.
5. Record whether attribution or license-preservation duties exist.
6. Record whether the source is safe for `ok`, or should stay
   `metadata_only`, `local_only`, `forbidden`, or `unknown`.
7. Record OCR usefulness and sensitivity risks in `notes`.

Recommended `notes` structure in `source_catalog.tsv`:

* `access=...`
* `license_basis=...`
* `commercial=...`
* `derivative=...`
* `attribution=...`
* `recommend=...`
* `useful=...`
* `review=...`
* `sample_download=...`

## Source Catalog vs Manifest

Default path:

* new web sources go to `source_catalog.tsv` first
* `manifest.tsv` is only for concrete candidate rows that we may later download,
  render, or stage locally
* if a source is too unclear, too large, or too sensitive, keep it in
  `source_catalog.tsv` and list row ideas in `audit_report.md` instead of
  forcing manifest rows

## Adding A Sample

Recommended workflow:

1. Add or update a source row in `source_catalog.tsv`.
2. Decide whether the source is `ok`, `metadata_only`, `local_only`,
   `forbidden`, or `unknown`.
3. If a concrete row is worth tracking, add a planning row to `manifest.tsv`.
4. Put commit-safe payload files under `samples/<scenario>/` and keep
   non-committable payloads only under `local_only/`.
5. Record scenario tags, risk tags, expected preview notes, expected hint notes,
   and `sha256` once a file exists.
6. Keep provider-generated artifacts local unless the payload itself is clearly
   review-safe.

Suggested row id style:

* lowercase
* words separated by `_`
* short scenario cues such as `cand_irs_w4_blank_page`

## Recording SHA256

From the main repo root, for a local payload file:

```bash
shasum -a 256 markitdown-quality-lab/ocr_corpus/samples/layout/sample.png
```

Copy the hex digest into the `sha256` field only after the file exists.

## Running Existing OCR Quality Helpers

Current helpers still target `markitdown-quality-lab/ocr_samples/`, which
remains the checked-in synthetic/reference OCR surface. This audit directory is
upstream of that step and helps us decide which real-world rows are worth
curating next.

Useful existing commands from the main repo root:

```bash
bash samples/helpers/validation/check_quality_lab_ocr_scaffold.sh
bash samples/helpers/quality/summarize_quality_lab_ocr.sh
bash samples/helpers/quality/check_quality_lab_ocr_preview.sh
bash samples/helpers/quality/check_quality_lab_ocr_resegmented_preview.sh
bash samples/helpers/quality/check_quality_lab_ocr_ir_hints.sh
```

Interpretation:

* these helpers validate and compare the existing `ocr_samples` scaffold
* they are optional audit helpers, not a public-only gate
* `ocr_corpus` is a planning/audit surface and does not replace current helper
  inputs today

## Seed Preview Smoke

For tracked `ocr_corpus/samples/` files:

* use local `tesseract` smoke runs only as qualitative preview, not as product
  assertions
* keep preview text or provider outputs under `.tmp/ocr_corpus_preview/` or
  `local_only/`, never in tracked git paths
* if a row is `pdf_page_image` and current image-only smoke does not support the
  source format, record `skipped` in `audit_report.md` instead of forcing PDF
  OCR
* if language data is missing locally, record `not_run` or `weak` and describe
  the limitation in `audit_report.md`

## Local-Only Policy

Use `local_only/` for:

* private screenshots or phone captures
* real receipts, invoices, labels, addresses, signatures, or IDs
* samples with uncertain redistribution terms
* temporary provider outputs produced from non-committable inputs

Keep out of `local_only/`:

* anything that should be committed after review
* large mirrored datasets
* copied third-party license files that were not explicitly reviewed
