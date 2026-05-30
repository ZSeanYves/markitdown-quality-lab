# Footer Header Noise Manual Review Blocker

Date: 2026-05-31

## Decision

Blocker status: `waiting_for_manual_review`.

`footer_header_noise` remains report-only. It is not eligible for a runtime
hook, default model hook, or converter-path change until the external-quality
manual review is filled and summarized.

## Review Artifacts

Primary review package:

* review TSV:
  `pdf_model_training/text_block_classifier/local_only/reports/footer_header_manual_review/v1/footer_header_manual_review.tsv`
* visual review HTML:
  `pdf_model_training/text_block_classifier/local_only/reports/footer_header_manual_review/v1_visual/review_index.html`
* visual review Markdown:
  `pdf_model_training/text_block_classifier/local_only/reports/footer_header_manual_review/v1_visual/review_index.md`

Current local-only summary artifacts:

* summary report:
  `pdf_model_training/text_block_classifier/local_only/reports/footer_header_manual_review/v1/footer_header_manual_review_summary.md`
* summary TSV:
  `pdf_model_training/text_block_classifier/local_only/reports/footer_header_manual_review/v1/footer_header_manual_review_summary.tsv`

The visual pack is usable as the primary review surface:

* review rows: `58`
* resolved PDF paths: `58`
* unresolved PDF paths: `0`
* produced Markdown found: `58`
* metadata found: `58`
* rendered pages: `58`
* crops: `58`
* failed renders: `0`

## Reviewer Decision Status

The review TSV exists, but all `reviewer_decision` cells are blank:

| item | count |
| --- | ---: |
| total rows | 58 |
| reviewed rows | 0 |
| blank rows | 58 |
| emit rows | 6 |
| blocked rows | 52 |

Gate status distribution:

| gate status | count |
| --- | ---: |
| `label_not_allowed` | 25 |
| `blocked_model_confidence` | 14 |
| `blocked_hard_conflict` | 13 |
| `emit` | 6 |

Review bucket distribution:

| review bucket | count |
| --- | ---: |
| `blocked_body_text_risk` | 21 |
| `blocked_dense_edge_row` | 10 |
| `near_miss_high_confidence` | 8 |
| `blocked_low_confidence` | 6 |
| `emitted_page_number_like` | 6 |
| `blocked_label_not_allowed` | 4 |
| `other` | 3 |

## Summary Result

The current local-only summary recommendation is
`waiting_for_manual_review`.

Reasons:

* all `reviewer_decision` cells are blank
* reviewer decisions must be filled before any keep/refine/threshold/expand
  recommendation is meaningful
* no precision claim can be made from the current manual-review package

Valid review decisions are intentionally explicit:

* emitted rows: `accept`, `reject`, `unsure`
* blocked rows: `keep_blocked`, `should_emit`, `needs_new_guard`,
  `out_of_scope`

## Next Command

First, open the visual review package and fill `reviewer_decision` and
`reviewer_notes` in the review TSV. Then summarize the completed review:

```bash
cd ~/Moonbit/markitdown/markitdown-quality-lab
python pdf_model_training/text_block_classifier/scripts/summarize_footer_header_manual_review.py \
  --review-tsv pdf_model_training/text_block_classifier/local_only/reports/footer_header_manual_review/v1/footer_header_manual_review.tsv \
  --output-report pdf_model_training/text_block_classifier/local_only/reports/footer_header_manual_review/v1/footer_header_manual_review_summary.md \
  --output-summary-tsv pdf_model_training/text_block_classifier/local_only/reports/footer_header_manual_review/v1/footer_header_manual_review_summary.tsv
```

After that summary is regenerated, the next decision should be one of:

* `needs_guard_refine` if emitted rows are rejected, blocked rows should emit
  unexpectedly, or new guard requests appear
* `eligible_for_report_only_proposal` only if manual review shows no emitted
  rejects, hard conflicts mostly stay blocked, near misses do not indicate a
  meaningful missing-emission cluster, and no new guard requests appear

## Boundaries

Do not change `footer_header_noise` gates from this blocker note.

Do not connect a runtime model hook, default-enable model hints, mutate
converter behavior, or update expected Markdown output from this package.

External-quality rows remain validation and report-only review rows. They are
not training gold.
