# OCR Corpus Audit

This directory exists only for OCR real-world quality audit work in
`markitdown-quality-lab`.

Scope:

* this directory is for curating and auditing real-world OCR sample candidates
* the goal is quality audit coverage for the shipped main-CLI image OCR path
* PDF OCR is out of scope for this round
* this directory does not define a product gate or public-only gate
* this directory does not change converter/runtime behavior and does not change
  OCR assertions

Current OCR boundary:

* shipped OCR currently means image OCR on the main CLI
* image OCR depends on local `tesseract` plus matching language data
* current OCR audit work helps us inspect provider signal, layout recovery,
  preview output, and future IR hints for image inputs
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
* tiny license-clean metadata-only notes that do not include payload bytes or
  unclear-license text

Do not commit:

* real sample files whose redistribution is not explicitly `ok`
* any local-only payload under `local_only/`
* provider outputs generated from local-only or unclear-license inputs
* copied license texts that have not been intentionally reviewed
* large downloads or bulk dataset mirrors

## Taxonomy

The current OCR audit taxonomy uses the following top-level scenario buckets:

* `plain_print`: clean printed text with straightforward reading order
* `layout`: multi-column, mixed alignment, headers/footers, captions, or
  reading-order stress
* `structured`: receipts, forms, tables, menus, labels, and other structured
  image documents
* `degradation`: blur, skew, low contrast, compression noise, glare, crop loss,
  or handwriting-over-print interference
* `language`: multilingual, mixed-script, non-Latin, vertical text, or language
  pack sensitivity checks
* `negative`: non-document images, decorative text, extremely low-signal inputs,
  or inputs where OCR should remain weak/ambiguous

These scenario labels are audit tags only. They do not guarantee Markdown
reconstruction quality, and they do not imply that `TableLike`, `KeyValueLike`,
or `CaptionLike` hints are product guarantees.

## Redistribution Policy

Allowed `redistribution` values:

* `ok`: payload may be checked in after review
* `metadata_only`: keep only manifest/catalog metadata in git
* `local_only`: payload may be stored locally for audit but must stay out of git
* `forbidden`: do not store payload in git or local shared corpus; keep at most
  a note explaining why it was rejected
* `unknown`: not reviewed yet; treat like non-committable until clarified

Rules:

* default to `unknown` when terms are unclear
* only `ok` is eligible for tracked payload bytes
* `metadata_only` rows may appear in tracked manifests, but payload paths should
  stay empty or point to future reviewed assets
* `local_only` rows belong under `local_only/` and that subtree is git-ignored
* `forbidden` rows belong only in audit notes, not in the active payload pool

## Files

* `source_catalog.tsv`
  Source-level audit catalog for candidate corpora, websites, datasets, and
  manually curated local collections.
* `manifest.tsv`
  Canonical tracked manifest for reviewed OCR corpus rows that are safe to
  describe in git.
* `manifest.example.tsv`
  Example row template showing recommended field usage.
* `audit_report.md`
  Working audit summary: scope, accepted/rejected source classes, sample
  targets, and next actions.
* `local_only/`
  Git-ignored area for local manifests and payloads that cannot be committed.

## Manifest Fields

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

* `relative_path` should be repo-relative under `ocr_corpus/` and must never be
  absolute or contain `..`
* `relative_path` may be blank for tracked metadata-only placeholder rows that
  intentionally do not carry payload bytes yet
* `local_only` must be `true` only for local manifests or payload references
* `scenario` should use one or more taxonomy tags such as
  `layout;structured`
* `risk_tags` can record privacy, license, or content concerns such as
  `pii_possible`, `license_review`, `screenshot`, or `non_doc_negative`
* `expected_preview` is a compact expectation for layout-preview review, not a
  formal assertion
* `expected_hints` is a compact expectation for semantic/layout hint review, not
  a product guarantee
* `sha256` should be recorded for any real payload file once staged locally

## Adding A Sample

Recommended workflow:

1. Add or update a source row in `source_catalog.tsv`.
2. Decide whether the source is `ok`, `metadata_only`, `local_only`,
   `forbidden`, or `unknown`.
3. If the payload cannot be redistributed, keep the bytes under `local_only/`
   only and use a local manifest row there instead of adding tracked payload
   files.
4. Add a row to `manifest.tsv` only when it is safe to describe in git.
5. Record scenario tags, risk tags, expected preview notes, expected hint notes,
   and `sha256`.
6. Keep provider-generated artifacts local unless the payload itself is clearly
   review-safe.

Suggested sample id style:

* lowercase
* words separated by `_`
* include a short source or scenario cue such as
  `receipt_cn_blur_local_001`

## Recording SHA256

From the main repo root, for a local payload file:

```bash
shasum -a 256 markitdown-quality-lab/ocr_corpus/local_only/path/to/sample.png
```

Copy the hex digest into the `sha256` field. If the payload is not present in
git, keep only the digest plus metadata in the appropriate manifest.

## Running Existing OCR Quality Helpers

Current helpers target `markitdown-quality-lab/ocr_samples/`, which remains the
checked-in synthetic/reference OCR surface. This audit directory is upstream of
that step and helps us decide which real-world rows are worth curating next.

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
* this `ocr_corpus` directory should feed future curated additions, but does not
  replace current helper inputs today

## Local-Only Policy

Use `local_only/` for:

* private screenshots
* samples with uncertain redistribution terms
* samples containing potential personal data
* temporary provider outputs produced from non-committable inputs

Keep out of `local_only/`:

* anything that should be committed after review
* large mirrored datasets
* copied third-party license files that were not explicitly reviewed
