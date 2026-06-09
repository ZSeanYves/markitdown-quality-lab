# text_block_classifier Feature Contract

Layer:

* PDF convert layer

Consumer:

* convert-owned IR and Markdown decisions

## Boundary

The `text_block_classifier` consumes parser-produced text, geometry, style,
neighbor, and optional parser-owned layout hints. It emits semantic soft hints,
confidence, and abstain flags for convert-layer use.

It must not consume convert output labels, Markdown/IR decisions, or classifier
predictions from an earlier pass as model input features. That would invert the
architecture and make evaluation look cleaner than runtime.

The high-confidence gate may consume only:

* parser/model features
* classifier probability, confidence, and margin
* static runtime gate thresholds

The high-confidence gate must not consume Markdown/IR output, post-conversion
labels, or manually corrected runtime decisions.

## Current Baseline Feature Set

Current checked reports use local-only DocLayNet `pilot3000_v1` feature set
`baseline_v3`.

Available feature families:

| family | examples | status |
| --- | --- | --- |
| provenance/source | `source_dataset`, `source_label`, `target_label`, `split` | audit only, not model features |
| text shape | `text_len`, `token_count`, `title_token_ratio`, `upper_ratio`, `ends_period` | already_available |
| bbox geometry | `bbox_x_norm`, `bbox_y_norm`, `bbox_w_norm`, `bbox_h_norm`, `bbox_area_norm` | already_available |
| page position | `near_top`, `near_bottom`, `page_position_bucket_fine` | already_available |
| spacing/indent | `left_indent_bucket`, `indent_bucket_fine`, `prev_gap_norm`, `next_gap_norm` | already_available |
| neighbor context | `prev_text_len_norm`, `next_text_len_norm`, `prev_width_ratio`, `next_width_ratio` | weak proxy |
| list pattern | `starts_bullet`, `starts_numbered`, `rich_list_marker_type`, `starts_with_roman_marker` | already_available |
| heading shape | `heading_like_short`, `isolated_heading_like`, `section_prefix_depth` | weak proxy |
| caption association | `starts_with_caption_cue`, `caption_near_prev_wide`, `prev_has_figure_cue` | weak proxy |
| font/style | font size/name/weight deltas | not_available_yet |
| visual proximity | true image/table/figure region distance | requires_parser_export |
| layout_recovery hints | region/risk/reading-order hints | requires_layout_recovery_hint |

## candidate_iter3_features

The iteration 3 candidate set is split by availability rather than by model
wish list.

### already_available

| feature | source columns |
| --- | --- |
| `bullet_or_number_prefix` | `starts_bullet`, `starts_numbered`, `list_marker_type`, `rich_list_marker_type` |
| `left_indent_bucket` | `left_indent_bucket`, `indent_bucket_fine` |
| `caption_prefix_binary` | `starts_with_caption_cue` |
| `caption_like_short` | `caption_like_short` |
| `titlecase_ratio` | `title_token_ratio` |
| `uppercase_ratio` | `upper_ratio`, `all_caps_ratio` |
| `ends_with_period` | `ends_period`, `has_terminal_period` |
| `section_number_prefix` | `section_number_prefix`, `section_prefix_depth` |

### derived_from_existing_features

| feature | derivation |
| --- | --- |
| `caption_prefix_pattern` | regex enum from `text` |
| `text_length_bucket` | bucket from `token_count` or text token count |
| `starts_with_enumeration_pattern` | regex boolean from `text` |
| `enumeration_prefix_kind` | bullet/decimal/alpha/roman/paren enum from `text` |
| `short_text_score` | graded score from token-count bucket |
| `caption_keyword_score` | text cue score from caption/table/figure prefixes |
| `line_start_pattern` | compact enum from marker regexes |

### requires_parser_export

| feature | required parser signal |
| --- | --- |
| `near_image_or_table_region` | image/table/figure region geometry |
| `distance_to_previous_visual_region` | ordered visual/table/figure regions on page |
| `distance_to_next_visual_region` | ordered visual/table/figure regions on page |
| `below_image_or_table` | block-vs-visual vertical relation |
| `above_table_or_figure` | block-vs-visual vertical relation |
| `same_page_visual_density` | page-level visual/table/figure inventory |
| `hanging_indent_score` | line-level indent and baseline data |
| `continuation_line_count` | parser line grouping inside block |
| `wrapped_line_candidate` | parser line-break and merge evidence |
| `font_size_delta_to_page_median` | dominant font size and page median |
| `font_size_delta_to_neighbor_body` | font size plus neighbor body density |
| `body_density_after` | parser text/line density after candidate |
| `neighbor_body_density` | parser-derived neighbor density, not predicted labels |

### requires_layout_recovery_hint

| feature | required hint |
| --- | --- |
| `region_label_hint` | high-confidence parser-owned region type |
| `caption_visual_association_hint` | parser/layout confidence that caption belongs to figure/table |
| `reading_order_risk` | parser-owned low-confidence order/risk flag |
| `multi_column_risk` | parser-owned column ambiguity flag |

### not_available_yet

These should not be faked from convert outputs:

* true font/style deltas
* true image/table/figure proximity
* true line-level continuation counts
* body-density features based on predicted paragraph labels

## Minimum Next-Train Feature Set

The smallest useful next train should add only features that are either already
available or cheaply derived, while recording parser-export blockers.

caption:

* `caption_prefix_pattern`
* `text_length_bucket`
* `page_position_bucket`
* `near_visual_region_proxy` if available

list:

* `bullet_or_number_prefix`
* `enumeration_prefix_kind`
* `left_indent_bucket`
* `continuation_line_count` if available

heading:

* `font_size_delta` when parser export exists
* `titlecase_ratio`
* `uppercase_ratio`
* `ends_with_period`
* `section_number_prefix`
* `neighbor_body_density` when parser export exists

## Outputs

Allowed output families:

* block semantic role labels
* soft hints and confidence scores
* abstain or low-confidence flags

Primary labels:

* `heading`
* `paragraph`
* `caption`
* `table_like`
* `list_item`
* `footer_header_noise`
* `form_row`
* `link_text`
* `keep_as_text`
* `code_like`
* `footnote_like`
* `page_number_noise`
* `separator`
* `uncertain`

## Runtime Boundary

The convert layer may use parser-owned layout signals as features. It must not
rewrite parser canonical layout or feed semantic labels back into parser layout
recovery.

Heavy teacher checkpoints, generated full feature TSVs, prediction dumps, and
local eval reports remain external-only.
