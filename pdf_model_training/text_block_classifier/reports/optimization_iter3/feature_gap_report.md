# Feature Gap Report

## Inputs

- features: `pdf_model_training/text_block_classifier/local_only/features/doclaynet/pilot3000_v1/baseline_v3/features.tsv`
- split_filter: `heldout`
- rows_read: `11123`
- total_columns: `118`
- model_feature_columns: `107`

## Feature Families

| feature_family | columns |
| --- | --- |
| bbox geometry | 12 |
| caption association | 6 |
| heading shape | 4 |
| list pattern | 12 |
| neighbor context | 10 |
| page position | 8 |
| spacing/indent | 21 |
| text shape | 34 |

## Gap Status

| status | count |
| --- | --- |
| already_available | 11 |
| requires_parser_export | 3 |
| weak | 16 |

## Label Distributions

Source labels:

| source_label | count |
| --- | --- |
| Caption | 286 |
| Footnote | 232 |
| List-item | 3378 |
| Page-footer | 375 |
| Page-header | 320 |
| Section-header | 1546 |
| Table | 424 |
| Text | 4393 |
| Title | 169 |

Target labels:

| target_label | count |
| --- | --- |
| caption | 286 |
| footer_header_noise | 695 |
| heading | 1715 |
| keep_as_text | 232 |
| list_item | 3378 |
| paragraph | 4393 |
| table_like | 424 |

## Error Bucket Findings

### caption

| feature | status | available | requires | priority |
| --- | --- | --- | --- | --- |
| near_image_or_table_region | weak | caption_near_prev_wide,caption_near_next_wide,prev_has_table_cue,next_has_table_cue,prev_has_figure_cue,next_has_figure_cue | parser visual/table/figure region geometry | P0 |
| distance_to_previous_visual_region | weak | prev_gap_norm,prev_gap_bucket,caption_near_prev_wide | parser visual/table/figure region geometry | P0 |
| distance_to_next_visual_region | weak | next_gap_norm,next_gap_bucket,caption_near_next_wide | parser visual/table/figure region geometry | P1 |
| caption_prefix_pattern | already_available | starts_with_caption_cue |  | P0 |
| short_text_with_caption_keywords | already_available | caption_like_short |  | P1 |
| same_page_visual_density | requires_parser_export |  | parser page visual inventory | P1 |
| below_image_or_table | weak | caption_near_prev_wide,prev_has_table_cue,prev_has_figure_cue | parser visual/table/figure region geometry | P0 |
| above_table_or_figure | weak | caption_near_next_wide,next_has_table_cue,next_has_figure_cue | parser visual/table/figure region geometry | P1 |
| near_figure_region | weak | prev_has_figure_cue,next_has_figure_cue,starts_with_figure_cue | parser figure/image region geometry | P0 |
| near_table_region | weak | prev_has_table_cue,next_has_table_cue,starts_with_table_cue | parser table region geometry | P0 |
| caption_keyword_score | weak | starts_with_caption_cue,contains_figure_hint,contains_table_hint | text | P2 |

### list_item_vs_paragraph

| feature | status | available | requires | priority |
| --- | --- | --- | --- | --- |
| bullet_or_number_prefix | already_available | starts_bullet,starts_numbered,list_marker_type,rich_list_marker_type |  | P0 |
| starts_with_enumeration_pattern | already_available | starts_with_alpha_marker,starts_with_roman_marker,starts_with_paren_marker |  | P0 |
| left_indent_bucket | already_available | left_indent_bucket,indent_bucket_fine |  | P0 |
| hanging_indent_score | weak | continuation_indent_like,continuation_after_marker_prev,continuation_before_marker_next,prev_same_left_band,next_same_left_band | parser line-level indent and wrapped-line structure | P0 |
| continuation_line_count | weak | continuation_after_marker_prev,continuation_before_marker_next | parser line grouping | P0 |
| sibling_indent_similarity | weak | prev_same_left_band,next_same_left_band,prev_x_delta_bucket,next_x_delta_bucket | parser ordered sibling block/line context | P1 |
| wrapped_line_candidate | weak | continuation_indent_like,continuation_after_marker_prev,continuation_before_marker_next | parser line grouping | P0 |
| line_start_pattern | weak | starts_bullet,starts_numbered,starts_with_alpha_marker,starts_with_roman_marker,starts_with_paren_marker | text | P1 |
| numbering_prefix_kind | already_available | rich_list_marker_type,list_marker_type |  | P0 |

### paragraph_list_item_vs_heading

| feature | status | available | requires | priority |
| --- | --- | --- | --- | --- |
| font_size_delta_to_page_median | requires_parser_export |  | parser font/span style export | P0 |
| font_size_delta_to_neighbor_body | requires_parser_export |  | parser font/span style plus neighbor body density | P0 |
| short_text_score | already_available | short_text,very_short_text,token_count |  | P1 |
| titlecase_ratio | already_available | title_token_ratio |  | P1 |
| uppercase_ratio | already_available | upper_ratio,all_caps_ratio |  | P1 |
| ends_with_period | already_available | ends_period,has_terminal_period |  | P1 |
| body_density_after | weak | next_text_len_norm,text_density_bucket,next_overlap_ratio_bucket | parser line/block density around candidate | P0 |
| section_number_prefix | already_available | section_number_prefix,section_prefix_depth |  | P1 |
| neighbor_body_density | weak | prev_text_len_norm,next_text_len_norm,prev_width_ratio,next_width_ratio | parser neighbor paragraph density features | P0 |
| heading_shape_guard | weak | heading_like_short,heading_like_gap_before,heading_like_gap_after,isolated_heading_like | font/style and body-density signals | P0 |

## Interpretation

- Caption has text-cue and neighbor-text proxies, but no true image/table/figure proximity or visual density features.
- List-item vs paragraph has marker and indent features, but still lacks reliable line-level continuation and hanging-indent counts.
- Heading has text-shape and gap proxies, but no font-size delta or body-density guard.
- No feature may consume convert/Markdown/IR output labels as input; next features must come from parser geometry/text/style or classifier probability only.
