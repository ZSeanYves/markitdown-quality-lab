# Footer Header Noise Report-Only Package

## Goal

This package freezes the current external-quality cooperative gate setup for:

* `footer_header_noise`

It is intended for:

* report-only dry runs
* manual review preparation
* profile reuse across future external-quality PDF slices

It is not:

* runtime integration
* a convert-path mutation
* a parser/layout recovery route
* an approval to delete or relabel product text automatically

## Input Chain

The current report-only path is:

1. external-quality PDF rows
2. legacy PDF block candidates from the unchanged product path
3. tracked bridge into `baseline_v3`-compatible text-block features
4. offline `HGB` teacher predictions
5. cooperative gate scoring under `conservative_v2`

Current readiness:

* bridge compatibility: `ready`
* matched legacy feature rows: `360`
* output feature rows: `360`
* predicted label distribution is stable across `pdf_all_v2` and
  `pdf_all_v3_footer_refined`

## Recommended Profile

Recommended report-only profile:

* profile: `conservative_v2`
* `model_confidence_threshold = 0.95`
* `cooperative_threshold = 0.85`
* allowed emit label: `footer_header_noise` only

Why this is the current default:

* rules remain primary
* hard conflicts still block regardless of model confidence
* the profile removes the known `pdf_all_v2` false-positive booking-row cells
* the remaining emit surface stays narrow instead of collapsing to `0`

## v2 vs v3 Readout

| run | profile | candidates | emitted | hard_conflict | no_override | form_key_value emit | body-risk emit |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `pdf_all_v2` | `conservative` | 360 | 12 | 7 | 341 | 3 | 0 |
| `pdf_all_v3_footer_refined` | `conservative_v2` | 360 | 6 | 13 | 341 | 0 | 0 |

Other stable facts:

* selected rows: `77`
* processed rows: `76`
* skipped license rows: `1`
* predicted labels unchanged from `pdf_all_v2`:
  * `footer_header_noise = 53`
  * `heading = 167`
  * `paragraph = 109`
  * `table_like = 27`
  * `caption = 4`

## What Changed In v3

`pdf_all_v3_footer_refined` adds a narrower hard conflict:

* `dense_edge_row_conflict`

This conflict is meant to block:

* dense multi-column edge rows
* schedule/booking-like row cells
* short row-index-like cells that are structurally part of the same edge row

It is not meant to block:

* isolated page-number shells

Observed effect:

* `6` `pdf_all_v2` emits from the movie-booking edge row became
  `blocked_hard_conflict:dense_edge_row_conflict`
* the predicted label distribution did not change
* `form_key_value` emit count dropped from `3` to `0`
* body-risk emit count stayed at `0`

## Why `form_key_value` Is Not The Main Guard

`form_key_value` should not be promoted into a blanket hard conflict.

Reason:

* the suspicious booking row emitted both `form_key_value` cells like
  `7:00 PM` / `4:30 PM` / `9:30 PM`
* and non-`form_key_value` cells like `2`, `3`, and `12/26-12/31`

The stronger failure signal was row structure:

* edge position
* dense multi-column layout
* short cell-like text
* very small neighbor gaps

## Current Emit Surface

Current `pdf_all_v3_footer_refined` emits are all the same family:

* isolated page-number-style shells

Observed examples:

* `md_test_pdf`: `2`, `3`
* `pdf_section_numbering_markitdown_test`: `2`, `3`
* `pdf_tounicode_unicode_markitdown_test`: `2`, `3`

Current interpretation:

* this is still meaningful coverage for `footer_header_noise`
* it is narrow enough to keep the run fail-closed

## Current Non-Emit Surface

### No-Override Majority

The dominant `no_override` reasons remain:

* `label_not_allowed:heading = 167`
* `label_not_allowed:paragraph = 109`
* `confidence<0.95 = 34`
* `label_not_allowed:table_like = 27`
* `label_not_allowed:caption = 4`

Interpretation:

* most non-emits are label disagreement, not bridge failure
* the current runner should stay `footer_header_noise`-only
* `heading` and `keep_as_text` should be reviewed separately, not widened here

### Hard-Conflict Families

The current hard-conflict surface is dominated by two families:

* compact heading-shape shells such as `SCR-2`, `SCR-1`, `Winter Wonderland`,
  `New Year Mystery`, `PM`, `Total Revenue:`
* dense edge-row cells such as `7:00 PM`, `4:30 PM`, `9:30 PM`, `2`, `3`, and
  `12/26-12/31`

Interpretation:

* `heading_shape_conflict` still protects against strong title-like shells
* `dense_edge_row_conflict` closes the known movie-booking false-positive hole

## Current Risk Statement

This package is still report-only.

Current safety statement from `pdf_all_v3_footer_refined`:

* `central_body_band` / `sentence_like` / `long_text` body-risk rows remain
  `0 emit`
* there is no current evidence that broader body content is leaking into emit

Remaining open question before any future expansion:

* whether the isolated page-number-style emit surface stays clean on a larger
  and more source-diverse external-quality slice

Based on the current `pdf_all_v3_footer_refined` sample, there is no obvious
new guard to add before the next manual review stage.

## Manual Review Package v1

Current tracked exporter:

* `scripts/export_footer_header_manual_review.py`
* `scripts/summarize_footer_header_manual_review.py`
* `scripts/export_footer_header_review_visual_pack.py`

Current local-only outputs:

* `footer_header_manual_review.tsv`
* `footer_header_manual_review.md`
* `footer_header_manual_review_summary.tsv`
* `footer_header_manual_review_summary.md`
* `v1_visual/footer_header_manual_review.enriched.tsv`
* `v1_visual/review_index.md`
* `v1_visual/review_index.html`

Current review-row schema:

* `review_id`
* `row_id`
* `sample_id`
* `source_pdf_id`
* `page_no`
* `block_id`
* `bbox`
* `text_preview`
* `gate_status`
* `gate_action`
* `gate_reason`
* `predicted_label`
* `confidence`
* `cooperative_score`
* `risk_flags`
* `review_bucket`
* `suggested_manual_label`
* `reviewer_decision`
* `reviewer_notes`

Current review buckets:

* `emitted_page_number_like`
* `emitted_edge_noise_like`
* `blocked_dense_edge_row`
* `blocked_body_text_risk`
* `blocked_low_confidence`
* `blocked_label_not_allowed`
* `near_miss_high_confidence`
* `other`

Review intent:

* audit every current emit
* audit every current hard conflict
* sample the highest-confidence `no_override` rows before any broader claim
* prepare manual evidence without changing product output or gate behavior

Manual review workflow:

1. start from `scripts/export_footer_header_review_visual_pack.py`
2. open `v1_visual/review_index.md` or `v1_visual/review_index.html`
3. use the enriched row context instead of the bare TSV:
   * input PDF path
   * produced Markdown path
   * metadata path
   * page image / bbox crop when a renderer is available
   * per-review Markdown entry files
4. fill `reviewer_decision`
5. fill `reviewer_notes` for any keep/refine/expand evidence
6. run `scripts/summarize_footer_header_manual_review.py`
7. read the summary report and choose:
   * `keep profile unchanged`
   * `refine guard`
   * `adjust threshold`
   * `expand benchmark`
   * `pause`

Visual-pack fallback rule:

* the preferred audit surface is the visual pack, not the bare TSV
* if `PyMuPDF/fitz` is available, the visual pack should render page PNGs and
  bbox crops
* if `PyMuPDF/fitz` is missing, the visual pack should still export:
  * resolved PDF path
  * produced Markdown path
  * metadata path
  * open-command hints
  * review index and per-review entry files
* missing render capability must not block the report-only review package from
  being exported

Expected decision meanings:

* `emit` rows:
  * `accept`
  * `reject`
  * `unsure`
* blocked rows:
  * `keep_blocked`
  * `should_emit`
  * `needs_new_guard`
  * `out_of_scope`

Current no-review fallback:

* blank or empty `reviewer_decision` is treated as `blank`
* a fully blank package should summarize to `waiting_for_manual_review`
* no runtime, convert, or parser proposal should move forward until review rows
  are filled
* no runtime, convert, or parser proposal should move forward from a bare TSV
  review without the visual-pack context

Why this review stage is required:

* current results are still report-only
* clean local dry-run counts are not enough for a runtime proposal
* reviewers still need to confirm that:
  * emitted page-number-like shells are acceptable
  * dense edge-row blocks are doing the intended work
  * high-confidence `no_override` rows are being held back for the right reasons

## Next Evaluation Checklist

1. Reuse `conservative_v2` unchanged on a larger external-quality PDF slice.
2. Export the manual-review package and audit all emitted hints.
3. Audit the high-confidence `no_override` rows before changing any threshold.
4. If manual review stays clean, prepare a larger external-quality
   footer/header report-only benchmark.
5. If manual review finds a new false-positive cluster, refine guards again
   without widening labels.
6. Keep `heading` guard work separate from this package.
7. Keep `keep_as_text` guard work separate from this package and paused here.
8. Keep `PubTables` specialist work source-separated from this external-quality
   package.
9. Keep runtime proposals paused until after larger report-only evidence and
   explicit manual review.
