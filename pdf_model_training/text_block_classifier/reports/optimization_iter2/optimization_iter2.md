# Text Block Classifier Optimization Iteration 2

## Inputs

- run_id: `pilot3000_v1_hgb_baseline_v3`
- model_type: `sklearn_hist_gradient_boosting_balanced`
- split: `heldout`
- predictions: `pdf_model_training/text_block_classifier/local_only/reports/pilot3000_v1_hgb_baseline_v3/predictions.tsv`
- metrics: `pdf_model_training/text_block_classifier/local_only/reports/pilot3000_v1_hgb_baseline_v3/metrics.json`
- features: `pdf_model_training/text_block_classifier/local_only/features/doclaynet/pilot3000_v1/baseline_v3/features.tsv`
- model: `pdf_model_training/text_block_classifier/local_only/models/pilot3000_v1_hgb_baseline_v3/model.pkl`
- probability_source: `local_model_predict_proba`
- margin_available: `true`
- prediction_top1_mismatch_count: `0`
- warnings:
  - prediction TSV has no full class probability matrix

## Iteration 1 Comparison

- baseline heldout accuracy: `0.8269`
- baseline heldout macro F1: `0.8097`
- iteration 1 global threshold: `0.70`
- iteration 1 runtime precision: `0.9013`
- iteration 1 runtime coverage: `0.7905`
- iteration 1 abstain rate: `0.2095`

## Gate Results

- confidence-only best: threshold `0.70`, precision `0.9013`, coverage `0.7905`, abstain `0.2095`, accepted macro F1 `0.8862`.
- margin-only best: margin `0.50`, precision `0.9045`, coverage `0.7753`, abstain `0.2247`, accepted macro F1 `0.8884`.
- combined best: confidence `0.70`, margin `0.00`, precision `0.9013`, coverage `0.7905`, abstain `0.2095`, accepted macro F1 `0.8862`.
- combined sweep does not improve on confidence-only; the best pair uses margin `0.00`.
- reached `runtime high-confidence precision >= 0.90`: `true`.
- coverage delta vs iteration 1: `+0.0000`.
- margin-only reaches the precision target, but only by reducing coverage below confidence-only.
- macro F1 without abstain is unchanged because no model was retrained.

## Per-Label Confidence Thresholds

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

## Error Analysis Summary

- caption remains the weakest label: F1 `0.5849`, support `286`.
- list_item/paragraph/heading confusions remain the main blocker and require feature work, not just threshold tuning.
- Margin gating is useful for audit, but it does not improve the best coverage-at-target gate in this sweep.

Top heldout confusions at the selected gate:

| rank | gold | predicted | count | avg_conf | avg_margin | accepted_errors |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | list_item | paragraph | 484 | 0.7017 | 0.4567 | 240 |
| 2 | paragraph | list_item | 327 | 0.6656 | 0.4141 | 131 |
| 3 | list_item | heading | 242 | 0.6734 | 0.4603 | 113 |
| 4 | paragraph | heading | 218 | 0.6541 | 0.4344 | 93 |
| 5 | paragraph | caption | 110 | 0.6477 | 0.4019 | 46 |
| 6 | heading | list_item | 93 | 0.6044 | 0.3347 | 26 |
| 7 | heading | paragraph | 79 | 0.6563 | 0.4189 | 29 |
| 8 | caption | heading | 67 | 0.7086 | 0.5457 | 30 |
| 9 | paragraph | table_like | 41 | 0.8153 | 0.6711 | 30 |
| 10 | caption | paragraph | 38 | 0.6105 | 0.3538 | 9 |

## Recommendation

- Keep the current model as a gated soft-hint teacher; do not promote it to unconditional runtime behavior.
- Keep confidence-only threshold `0.70` as the selected gate for this iteration.
- Use stricter margin gates only as audit variants unless a runtime consumer explicitly prefers lower coverage for higher precision.
- Retrain next with targeted features for caption association, list continuation/indentation, and heading-shape guards.
- Do not retrain layout_recovery or connect this report to runtime in this iteration.
