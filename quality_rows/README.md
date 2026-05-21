# Quality Rows

This directory tracks the external/local quality-row baseline that is meant to
run against payloads in `../corpus/`.

## Files

* `manifest.tsv`
  Canonical tracked quality-row manifest for the local/full external baseline.
* `manifest.example.tsv`
  Example row template carried over from the main repository legacy workflow.
* `source_catalog.tsv`
  Source catalog migrated from the old `external_sources.tsv`.

## Path style

Rows in `manifest.tsv` should prefer corpus-root-relative payload paths under
`sources/...`.

Examples:

* `sources/pdfjs/pdf/forms/annotation-text-widget.pdf`
* `sources/qpdf/pdf/links/link-annots.pdf`
* `sources/csv-spectrum/csv/escaped_quotes.csv`

Legacy `.external/quality_corpus/...` paths remain fallback-only during the
migration window and should not be reintroduced as canonical row paths.

## Relationship to the main repository

The main repository keeps:

* `samples/quality_corpus/manifest.tsv` for a small repo-tracked public baseline
* the quality runner and signal/assertion implementation

This lab keeps:

* the tracked full/local external quality-row baseline
* the payload source catalog
* the external payload corpus
* the canonical home for lab-managed quality rows that used to live in the
  main repository's ignored local manifests

`manifest.tsv` here does not replace the main repo's public baseline. The main
repo runner can merge both surfaces:

* public baseline from the main repo
* local/full lab baseline from `markitdown-quality-lab/quality_rows/manifest.tsv`

## Policy

* quality assertions are still interpreted by the main repository runner
* this lab is not a release artifact
* the old main-repo
  `samples/quality_corpus/external_manifest.local.tsv` is now a legacy fallback,
  not the recommended long-term home for tracked external/local quality rows
* current migration dry-run result:
  * `292` rows converted to canonical `sources/...`
  * `0` rows still require compatibility-tree-only paths
  * `14` rows remain unchanged because they are repo-owned or non-external
  * `1` pending-review placeholder remains missing:
    `sources/paddleocr/ppstructure_reference.pdf`

## Validation

From the main repository root:

```bash
bash samples/quality_corpus/check.sh --corpus-root markitdown-quality-lab/corpus
bash samples/quality_corpus/check.sh --corpus-root markitdown-quality-lab/corpus --format pdf
```
