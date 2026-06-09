# Layout Recovery Readiness

Date:

```text
2026-06-09
```

## Current State

`layout_recovery` is scaffolded and parser-facing.

No new baseline model was trained in this step.

Small legacy manual boundary rows are preserved under:

```text
pdf_model_training/layout_recovery/archive/
```

They are historical reference rows only and are not the active training route.

## DocLayNet Support

Strong support:

* `title_region`
* `section_header_region`
* `text_region`
* `table_region`
* `figure_region`
* `caption_region`
* `header_footer_region`

Weak support:

* multi-column hints
* page number regions
* caption association
* low-signal or malformed layout risk

Not directly supported:

* cross-page merge or no-merge
* source-reference consistency
* parser block grouping
* line-to-block grouping
* true reading order

## Current Inputs Ready for Scaffold

Shared dataset hub:

```text
pdf_model_training/datasets/doclaynet/
```

Historical full local cache:

```text
pdf_model_training/text_block_classifier/local_only/datasets/doclaynet/cache/
```

Current label mapping:

```text
pdf_model_training/layout_recovery/manifests/label_mapping.tsv
```

## Validation Gates Before Training

* Build a DocLayNet region adapter that preserves upstream source labels.
* Keep gold DocLayNet eval separate from weak PubLayNet/PubTables data.
* Define reading-order and cross-page labels separately from DocLayNet region
  labels.
* Confirm no model output is wired into normal runtime.
* Keep model parameters, features, predictions, and training cache local-only.

## Runtime Boundary

Potential future runtime candidates are limited to high-confidence distilled
parser hints, such as obvious header/footer or page-number regions.

The following remain training/eval-only until a separate runtime contract:

* reading-order generalization
* cross-page merge/no-merge
* low-signal risk assessment
* multi-column risk
* noisy caption association
