# Text Block Classifier Optimization Iteration 3

## 1. Summary

Iteration 3 moves away from threshold and margin tuning. Iteration 2 showed that
margin gating is not the current bottleneck: confidence-only remains the best
coverage-at-target gate.

This iteration audits feature readiness and label mapping for the dominant
error buckets:

- `caption`
- `list_item -> paragraph`
- `paragraph -> list_item`
- `list_item -> heading`
- `paragraph -> heading`
- `paragraph -> caption`

No runtime integration and no model retraining were performed.

## 2. Iteration 1/2 Baseline Recap

Baseline heldout metrics:

| metric | value |
| --- | --- |
| accuracy | 0.8269 |
| macro F1 | 0.8097 |

Best confidence gate:

| threshold | precision | coverage | abstain | accepted macro F1 |
| --- | --- | --- | --- | --- |
| 0.70 | 0.9013 | 0.7905 | 0.2095 | 0.8862 |

Margin audit:

| gate | threshold | precision | coverage | result |
| --- | --- | --- | --- | --- |
| margin-only | 0.50 | 0.9045 | 0.7753 | higher precision, lower coverage |
| combined | confidence 0.70 + margin 0.00 | 0.9013 | 0.7905 | no gain over confidence-only |

High-confidence precision is good enough for conservative soft hints, but
macro F1 is still below `0.90`. The model is not a completed quality upgrade.

## 3. Feature Inventory

Feature TSV:

`pdf_model_training/text_block_classifier/local_only/features/doclaynet/pilot3000_v1/baseline_v3/features.tsv`

Heldout audit:

| item | count |
| --- | --- |
| rows | 11123 |
| TSV columns | 118 |
| model feature columns | 107 |

Feature families found:

| family | columns | readiness |
| --- | --- | --- |
| text shape | 34 | strong |
| spacing/indent | 21 | medium |
| list pattern | 12 | strong |
| bbox geometry | 12 | strong |
| neighbor context | 10 | medium |
| page position | 8 | strong |
| caption association | 6 | weak proxy |
| heading shape | 4 | weak proxy |
| font/style | 0 | missing |
| true visual proximity | 0 | missing |
| layout_recovery hints | 0 | missing |

## 4. Feature Gap Matrix

Detailed matrix:

`feature_gap_matrix.tsv`

Status summary:

| status | count |
| --- | --- |
| already_available | 11 |
| weak | 16 |
| requires_parser_export | 3 |

Important interpretation:

- Caption has text-cue and neighbor-text proxies, but no true image/table/figure proximity.
- List-item vs paragraph has marker and indent features, but lacks line-level continuation counts.
- Heading has short-text and gap proxies, but lacks font-size delta and body-density guards.

## 5. Label Mapping Audit

Detailed audit:

`label_mapping_audit.md`

Key decisions:

- Keep DocLayNet `Caption -> caption`, but treat caption as a low-coverage high-precision hint.
- Keep DocLayNet `List-item -> list_item`, but add continuation and hanging-indent risk features before changing labels.
- Keep DocLayNet `Title` and `Section-header -> heading`, but add heading shape guards before runtime promotion.
- Do not promote `page_number_noise` or `uncertain` to direct runtime action.
- Keep `form_row`, `link_text`, `code_like`, `separator`, and `footnote_like` report-only.

## 6. Proposed Iter3 Candidate Features

Derived from existing columns now:

| feature | purpose |
| --- | --- |
| `caption_prefix_pattern` | expose caption/table/figure prefix enum |
| `text_length_bucket` | caption and heading shape audit |
| `starts_with_enumeration_pattern` | list/paragraph separator |
| `enumeration_prefix_kind` | bullet/decimal/alpha/roman/paren detail |
| `titlecase_ratio` | heading guard |
| `uppercase_ratio` | heading guard |
| `ends_with_period` | heading false-positive guard |
| `section_number_prefix` | heading/list ambiguity |
| `short_text_score` | graded short-text signal |

Requires parser export:

| feature | blocker |
| --- | --- |
| `near_image_or_table_region` | no visual/table/figure region geometry in baseline_v3 |
| `distance_to_previous_visual_region` | no ordered visual region inventory |
| `distance_to_next_visual_region` | no ordered visual region inventory |
| `hanging_indent_score` | no line-level indent/baseline export |
| `continuation_line_count` | no line grouping inside block |
| `font_size_delta_to_page_median` | no font-size/style export |
| `font_size_delta_to_neighbor_body` | no font-size/style export |
| `body_density_after` | no parser body-density feature |
| `neighbor_body_density` | must be derived from parser text/geometry, not predicted labels |

## 7. Derived Feature Builder

Added:

`pdf_model_training/text_block_classifier/scripts/build_iter3_derived_features.py`

Generated small reports only:

- `derived_feature_schema.tsv`
- `derived_feature_preview.tsv`

The preview is capped at 200 rows and is not a full feature TSV.

## 8. Retraining

Retrained: no.

Reason:

- Iteration 3 only added a bounded preview builder, not a full training feature TSV.
- P0 blockers still require parser exports: visual proximity, line continuation, and font/style deltas.
- Training now would mostly repackage existing signals and would not address the known dominant errors.

Next reproducible train command after an iter3 full feature TSV exists:

```bash
python pdf_model_training/text_block_classifier/scripts/train_doclaynet_baseline.py \
  --features pdf_model_training/text_block_classifier/local_only/features/doclaynet/pilot3000_v1/iter3_candidate/features.tsv \
  --run-id pilot3000_v1_hgb_iter3_candidate_v1 \
  --output-root pdf_model_training/text_block_classifier/local_only \
  --feature-set-name iter3_candidate_v1 \
  --model-kind hist_gradient_boosting_balanced
```

Follow with the existing gate evaluator against the generated local-only
`predictions.tsv` and `metrics.json`.

## 9. Metrics If Retrained

Not applicable. No model was trained in this iteration.

## 10. Runtime Gate Recommendation

Keep the iteration 2 gate:

| gate | threshold | precision | coverage | abstain |
| --- | --- | --- | --- | --- |
| confidence-only | 0.70 | 0.9013 | 0.7905 | 0.2095 |

Caption currently can only be a low-coverage high-precision hint unless visual
proximity and caption association features are added.

List-item and paragraph need prefix + indent + continuation features. Heading
needs shape guards and should not rely only on font-like or short-text cues.

## 11. Next Iteration Plan

1. Add parser-exported visual/table/figure proximity signals for caption.
2. Add parser line-level continuation and hanging-indent signals for list items.
3. Add font-size/style delta and neighbor body-density signals for headings.
4. Build a full local-only `iter3_candidate` feature TSV.
5. Retrain HGB locally and compare no-abstain macro F1 plus gated precision/coverage.

## 12. Blockers

- No true visual/table/figure region proximity in baseline_v3.
- No line-level continuation count or hanging-indent score.
- No font size/name/style export.
- No body-density guard independent of predicted labels.
- Macro F1 is still `0.8097`; it must not be described as `>=0.90`.
- High-confidence gate success only proves conservative runtime hint viability, not full model completion.
