# Text Block Classifier Training Loop Status

Date:

```text
2026-06-09
```

## Current Best Local Subset

```text
selection: doclaynet_pilot3000_v1
rows: 82373
train/dev/heldout: 60447 / 10803 / 11123
feature_set: baseline_v3
```

Local-only inputs:

```text
pdf_model_training/text_block_classifier/local_only/adapter_outputs/doclaynet/pilot3000_v1/task_a_rows.tsv
pdf_model_training/text_block_classifier/local_only/features/doclaynet/pilot3000_v1/baseline_v3/features.tsv
```

## Existing Baseline Iterations

| run | model kind | train macro F1 | dev macro F1 | heldout macro F1 | heldout accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| `pilot3000_v1_lr_baseline_v3` | logistic regression balanced | 0.7163 | 0.6748 | 0.6559 | 0.6875 |
| `pilot3000_v1_rf_baseline_v3` | random forest balanced | 0.9903 | 0.8270 | 0.7880 | 0.8125 |
| `pilot3000_v1_hgb_baseline_v3` | hist gradient boosting balanced | 0.9692 | 0.8311 | 0.8097 | 0.8269 |

Current best teacher line:

```text
pilot3000_v1_hgb_baseline_v3
```

Local-only report paths:

```text
pdf_model_training/text_block_classifier/local_only/reports/pilot3000_v1_lr_baseline_v3/metrics.json
pdf_model_training/text_block_classifier/local_only/reports/pilot3000_v1_rf_baseline_v3/metrics.json
pdf_model_training/text_block_classifier/local_only/reports/pilot3000_v1_hgb_baseline_v3/metrics.json
```

Local-only model paths:

```text
pdf_model_training/text_block_classifier/local_only/models/pilot3000_v1_lr_baseline_v3/model.pkl
pdf_model_training/text_block_classifier/local_only/models/pilot3000_v1_rf_baseline_v3/model.pkl
pdf_model_training/text_block_classifier/local_only/models/pilot3000_v1_hgb_baseline_v3/model.pkl
```

## High-Confidence Hint Status

Existing distillation v0 on heldout:

| threshold | emitted rows | coverage | emitted accuracy | wrong emitted |
| ---: | ---: | ---: | ---: | ---: |
| 0.90 | 6108 | 0.5491 | 0.9561 | 268 |
| 0.95 | 4676 | 0.4204 | 0.9737 | 123 |

Existing distillation v1 gated heldout result:

| threshold | emitted rows | coverage | emitted accuracy | wrong emitted |
| ---: | ---: | ---: | ---: | ---: |
| 0.95 | 1219 | 0.1096 | 0.9779 | 27 |

Strongest current runtime-distillation candidate:

```text
footer_header_noise
```

Labels requiring more guards or report-only handling:

* `heading`
* `keep_as_text`
* `list_item`
* `paragraph`
* `table_like`
* `caption`
* `form_row`
* `link_text`
* `code_like`
* `footnote_like`
* `page_number_noise`
* `separator`

## Risks

* Teacher metrics do not automatically imply runtime eligibility.
* Caption behavior needs association review, not only region-label accuracy.
* `paragraph` and `list_item` remain a major confusion pair.
* `heading` can over-fire on paragraph-like text without additional guards.
* Some TSV text fields can contain embedded newlines; use a TSV parser for
  row-count validation.
* RF model artifacts are large and must remain ignored local-only files.

## Next Validation Gates

* Keep DocLayNet gold heldout separate from weak-source experiments.
* Add per-label high-confidence precision/coverage gates before runtime
  proposals.
* Export reviewed error clusters for heading/list/paragraph confusions.
* Keep all model parameters and prediction dumps external-only.
