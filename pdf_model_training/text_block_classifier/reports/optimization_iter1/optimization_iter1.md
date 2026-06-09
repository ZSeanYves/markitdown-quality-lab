# Text Block Classifier Optimization Iteration 1

## Inputs

- run_id: `pilot3000_v1_hgb_baseline_v3`
- model_type: `sklearn_hist_gradient_boosting_balanced`
- split: `heldout`
- predictions: `markitdown-quality-lab/pdf_model_training/text_block_classifier/local_only/reports/pilot3000_v1_hgb_baseline_v3/predictions.tsv`
- metrics: `markitdown-quality-lab/pdf_model_training/text_block_classifier/local_only/reports/pilot3000_v1_hgb_baseline_v3/metrics.json`
- margin_available: `false`

## Baseline Without Abstain

- heldout accuracy: `0.8269`
- heldout macro F1: `0.8097`

Weakest labels by no-abstain F1:

| label | support | precision | recall | f1 |
| --- | --- | --- | --- | --- |
| caption | 286 | 0.5631 | 0.6084 | 0.5849 |
| keep_as_text | 232 | 0.8261 | 0.7371 | 0.7790 |
| heading | 1715 | 0.7331 | 0.8793 | 0.7996 |
| list_item | 3378 | 0.8503 | 0.7783 | 0.8127 |
| paragraph | 4393 | 0.8472 | 0.8329 | 0.8400 |

Full no-abstain per-label metrics:

| label | support | precision | recall | f1 |
| --- | --- | --- | --- | --- |
| heading | 1715 | 0.7331 | 0.8793 | 0.7996 |
| paragraph | 4393 | 0.8472 | 0.8329 | 0.8400 |
| caption | 286 | 0.5631 | 0.6084 | 0.5849 |
| table_like | 424 | 0.8643 | 0.9009 | 0.8822 |
| list_item | 3378 | 0.8503 | 0.7783 | 0.8127 |
| footer_header_noise | 695 | 0.9684 | 0.9712 | 0.9698 |
| keep_as_text | 232 | 0.8261 | 0.7371 | 0.7790 |

Secondary target:

* Heldout macro F1 target `>=0.90` is not met.
* Do not present this as a completed model-quality upgrade; use the gate as a safety filter and continue optimization.

## Global High-Confidence Gate

- target precision: `0.90`
- selected threshold: `0.70`
- runtime high-confidence precision: `0.9013`
- runtime high-confidence coverage: `0.7905`
- runtime abstain rate: `0.2095`
- meets target: `true`

Global sweep:

| threshold | precision | coverage | abstain | emitted |
| --- | --- | --- | --- | --- |
| 0.50 | 0.8496 | 0.9460 | 0.0540 | 10522 |
| 0.55 | 0.8631 | 0.9093 | 0.0907 | 10114 |
| 0.60 | 0.8773 | 0.8702 | 0.1298 | 9679 |
| 0.65 | 0.8887 | 0.8327 | 0.1673 | 9262 |
| 0.70 | 0.9013 | 0.7905 | 0.2095 | 8793 |
| 0.75 | 0.9146 | 0.7429 | 0.2571 | 8263 |
| 0.80 | 0.9271 | 0.6955 | 0.3045 | 7736 |
| 0.85 | 0.9389 | 0.6367 | 0.3633 | 7082 |
| 0.90 | 0.9544 | 0.5601 | 0.4399 | 6230 |
| 0.95 | 0.9723 | 0.4289 | 0.5711 | 4771 |

Interpretation:

* The runtime-eligible high-confidence precision target is met at threshold `0.70`.
* Coverage at that target is `0.7905`, so low-confidence rows abstain instead of forcing labels.
* Margin thresholding was not evaluated because the prediction file has no top1/top2 margin column.

## Label Gate Readiness

| label | threshold | precision | recall_on_gold | emitted | meets_target |
| --- | --- | --- | --- | --- | --- |
| heading | 0.85 | 0.9080 | 0.6618 | 1250 | true |
| paragraph | 0.70 | 0.9109 | 0.7125 | 3436 | true |
| caption | 0.95 | 0.9053 | 0.3007 | 95 | true |
| table_like | 0.75 | 0.9010 | 0.8373 | 394 | true |
| list_item | 0.60 | 0.9020 | 0.6978 | 2613 | true |
| footer_header_noise | 0.50 | 0.9768 | 0.9698 | 690 | true |
| page_number_noise | 0.50 | 0.0000 | 0.0000 | 0 | false |
| keep_as_text | 0.75 | 0.9130 | 0.6336 | 161 | true |
| uncertain | 0.50 | 0.0000 | 0.0000 | 0 | false |

Runtime labels not suitable for a runtime gate this round:

* `page_number_noise`
* `uncertain`

Labels that should continue as report-only:

* `code_like`
* `footnote_like`
* `form_row`
* `link_text`
* `separator`

## Confusion Highlights

| rank | gold | predicted | count | avg_conf | high_conf_errors |
| --- | --- | --- | --- | --- | --- |
| 1 | list_item | paragraph | 484 | 0.7017 | 240 |
| 2 | paragraph | list_item | 327 | 0.6656 | 131 |
| 3 | list_item | heading | 242 | 0.6734 | 113 |
| 4 | paragraph | heading | 218 | 0.6541 | 93 |
| 5 | paragraph | caption | 110 | 0.6477 | 46 |
| 6 | heading | list_item | 93 | 0.6044 | 26 |
| 7 | heading | paragraph | 79 | 0.6563 | 29 |
| 8 | caption | heading | 67 | 0.7086 | 30 |
| 9 | paragraph | table_like | 41 | 0.8153 | 30 |
| 10 | caption | paragraph | 38 | 0.6105 | 9 |

## Error Buckets

| rank | gold | predicted | bucket | count | next_action |
| --- | --- | --- | --- | --- | --- |
| 1 | list_item | paragraph | 0.50-0.70 | 187 | feature: strengthen list markers, indentation, and continuation context |
| 2 | list_item | paragraph | 0.70-0.90 | 158 | feature: strengthen list markers, indentation, and continuation context |
| 3 | paragraph | list_item | 0.50-0.70 | 134 | feature: strengthen list markers, indentation, and continuation context |
| 4 | list_item | heading | 0.70-0.90 | 98 | feature/data: add heading-shape guards and clean title-vs-body ambiguity |
| 5 | list_item | heading | 0.50-0.70 | 86 | feature/data: add heading-shape guards and clean title-vs-body ambiguity |
| 6 | list_item | paragraph | >=0.90 | 82 | feature: strengthen list markers, indentation, and continuation context |
| 7 | paragraph | list_item | 0.70-0.90 | 81 | feature: strengthen list markers, indentation, and continuation context |
| 8 | paragraph | heading | 0.50-0.70 | 64 | feature/data: add heading-shape guards and clean title-vs-body ambiguity |
| 9 | paragraph | list_item | <0.50 | 62 | feature: strengthen list markers, indentation, and continuation context |
| 10 | paragraph | heading | <0.50 | 61 | feature/data: add heading-shape guards and clean title-vs-body ambiguity |
| 11 | paragraph | heading | 0.70-0.90 | 59 | feature/data: add heading-shape guards and clean title-vs-body ambiguity |
| 12 | list_item | paragraph | <0.50 | 57 | feature: strengthen list markers, indentation, and continuation context |

## Next Optimization Direction

* Start with threshold tuning and per-label abstain thresholds; they directly improve safety without retraining.
* Add margin/probability output in the next prediction export so margin gating can be evaluated.
* Improve features for list-vs-paragraph continuation, heading shape, and caption association.
* Review label mapping and data cleaning for the weakest labels before changing class weighting.
* Do not connect this teacher or its reports to runtime until a separate runtime contract is written.
