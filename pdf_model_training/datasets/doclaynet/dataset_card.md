# DocLayNet Dataset Card

## Purpose

DocLayNet is the primary public gold source for the PDF two-model training
track. It provides human-annotated page layout regions that can be adapted into
parser-layer layout recovery targets and convert-layer text block targets.

## Current Local Cache

Observed local cache:

```text
pdf_model_training/text_block_classifier/local_only/datasets/doclaynet/cache/
```

Observed payloads:

```text
DocLayNet_core.zip
DocLayNet_extra.zip
```

Observed size during the 2026-06-09 audit:

```text
36G
```

The cache is intentionally ignored by git.

## Supported Targets

Strong direct support:

* page and region boxes
* table regions
* picture or figure regions
* caption regions
* page header and footer regions
* text, title, and section-header regions

Weak or indirect support:

* multi-column hints
* artifact or noise regions beyond page header/footer
* caption association
* page-number style noise

Not directly supported:

* cross-page merge or no-merge decisions
* parser source-reference consistency
* parser text-block grouping
* line-to-block grouping
* true reading order
* form rows
* link text
* code-like blocks
* Markdown section-title intent

## Local-Only Policy

Raw and extracted DocLayNet bytes stay local-only. Tracked files may reference
relative paths and counts, but must not include the dataset bytes themselves.

Future derived subsets should use stable names:

* `pilot500_v1`
* `pilot1000_v1`
* `pilot3000_v1`

Each derived subset should record:

* source zip/cache path
* adapter version
* split counts
* label mapping version
* feature-set version if features were exported
* report path for any model run
