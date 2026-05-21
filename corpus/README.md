# Quality Corpus

`corpus/sources/...` is the canonical location for external quality payloads.

## Canonical manifest path style

Local external-quality manifests should prefer corpus-root-relative paths under
`sources/...`.

Examples:

* `sources/pdfjs/pdf/forms/annotation-text-widget.pdf`
* `sources/qpdf/pdf/links/link-annots.pdf`
* `sources/csv-spectrum/csv/escaped_quotes.csv`

These are relative to the quality-lab corpus root:

```text
markitdown-quality-lab/
  corpus/
    sources/...
```

## Legacy migration

Older local manifests used legacy paths like:

* `.external/quality_corpus/pdf_external/pdfjs/annotation-text-widget.pdf`
* `.external/quality_corpus/pdf_external/qpdf/link-annots.pdf`
* `.external/quality_corpus/csv_external/csv-spectrum/escaped_quotes.csv`

Canonical manifests should migrate those to `sources/...` paths instead of
reintroducing legacy `.external/quality_corpus/...` entries.

The main repository still has a one-cycle fallback for legacy
`.external/quality_corpus/...` paths. This lab keeps a compatibility tree under
`corpus/` so the main repo can resolve legacy local-manifest paths during the
migration window without changing assertion semantics.

## Current dry-run status

The current main-repo dry-run for
`samples/quality_corpus/external_manifest.local.tsv` produced:

* `292` rows converted to canonical `sources/...`
* `0` rows requiring compatibility-only paths
* `14` unchanged repo/non-external paths
* `1` missing placeholder:
  `sources/paddleocr/ppstructure_reference.pdf`

That remaining PaddleOCR path is a `pending_review` placeholder rather than a
path-migration failure.

## Validation from the main repository

From `markitdown/`:

```bash
bash samples/quality_corpus/check.sh --corpus-root markitdown-quality-lab/corpus
bash samples/quality_corpus/check.sh --corpus-root markitdown-quality-lab/corpus --format pdf
```

## Policy

* `samples/quality_corpus/external_manifest.local.tsv` remains local-only in
  the main repository
* `corpus/MANIFEST.tsv` is the payload source-of-truth for this lab
* quality assertions stay in the main repository, not in this lab
* canonical manifest paths should prefer `sources/...`, not legacy
  `.external/quality_corpus/...`
