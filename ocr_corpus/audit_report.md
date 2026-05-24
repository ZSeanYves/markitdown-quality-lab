# OCR Real-World Audit Report

## Current Scope

* real-world OCR corpus audit for the shipped main-CLI image OCR path
* focus on sample discovery, taxonomy, license review, and manifest discipline
* no converter/runtime changes
* no OCR assertion changes
* no PDF OCR work in this round
* no packaging, announcement, or declaration-material work in this directory

## Accepted Source Classes

* self-generated image samples with project-safe text and layout
* locally captured document photos or screenshots kept under `local_only/`
* public web or dataset references recorded as metadata when redistribution is
  unclear
* small, intentionally reviewed third-party samples only after asset-level
  license confirmation

## Rejected Source Classes

* bulk dataset mirrors or large downloads
* samples with unclear or contradictory redistribution terms
* files containing obvious personal data unless they remain strictly local and
  intentionally reviewed
* PDF OCR payload plans for this round
* any source class that would turn OCR audit into a public-only quality gate

## P0 Sample Targets

* `plain_print`: 2 to 3 clean printed rows across English and Chinese
* `layout`: 2 to 3 rows covering two-column order, repeated header/footer, and
  caption-adjacent text
* `structured`: 2 to 3 rows covering receipt, invoice, and simple form layouts
* `negative`: at least 1 row showing non-document or weak-text behavior

## P1 Sample Targets

* `degradation`: 2 to 3 rows covering blur, skew, low contrast, or glare
* `language`: 2 to 3 rows covering multilingual or mixed-script text with
  explicit OCR language-pack notes
* local-only camera captures that help compare preview quality against the
  current synthetic `ocr_samples` set

## P2 Sample Targets

* more difficult structured images with dense field/value clustering
* long-tail negative rows that help spot over-claim risk
* carefully reviewed third-party `ok` rows if we later find redistribution-safe
  public examples worth tracking

## Open Questions

* whether future helper scripts should validate `ocr_corpus` metadata directly
  without requiring payload bytes
* how much of `ocr_corpus` should be mirrored into `ocr_samples` after a sample
  becomes license-clean and useful for stable checked-in comparisons
* whether we want a separate local manifest for provider outputs derived from
  non-committable inputs
* which multilingual rows best exercise `--ocr-lang` without creating a formal
  language-coverage promise

## Next Action Checklist

* add 3 to 5 local-only pilot rows with sha256 and scenario tags
* review one candidate source per taxonomy bucket for redistribution status
* keep provider outputs local for any non-`ok` payload
* promote only clearly reviewed rows into future checked-in OCR sample surfaces
* avoid wording that implies Markdown reconstruction guarantees from semantic
  hint names
