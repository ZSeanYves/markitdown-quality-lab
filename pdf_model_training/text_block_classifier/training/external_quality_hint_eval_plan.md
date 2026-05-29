# External Quality Hint Eval Plan

## Goal

This plan describes a future report-only evaluation path for distillation v1
hints on external PDF quality rows.

This plan does not:

* change product output
* mutate expected files
* affect `samples/check_quality.sh`
* propose runtime integration

## Inputs Needed

The current report-only runner now uses:

* converted PDF block candidates from the normal product path
* `legacy_features/*.features.tsv` side-channel block exports
* a tracked bridge into `baseline_v3`-compatible text-block features
* offline `HGB` teacher predictions
* cooperative gate scoring for `footer_header_noise`

Optional inputs for later expansion:

* more explicit adapter-like block rows for bbox/text alignment
* richer conflict summaries from deterministic rules

## Evaluation Contract

The runner should stay report-only.

Expected outputs:

* hint report
* conflict report
* `no_override` counts
* blocked-by-reason counts
* potential regression candidate list

It must not:

* rewrite Markdown output
* rewrite metadata output
* change quality assertions
* change baseline pass/fail criteria

## Proposed Flow

1. run the normal PDF quality pipeline unchanged
2. collect block candidates and feature rows in a side channel
3. apply the v1 gated hint evaluator in report-only mode
4. summarize:
   * emitted hint count
   * label distribution
   * blocked reasons
   * conflicts with deterministic rules
   * suspicious rows for manual review
5. compare the report against the original quality run without mutating outputs

## Current Scaffold Status

Current tracked runner:

* `scripts/run_external_quality_hint_dry_run.py`
* `scripts/export_footer_header_manual_review.py`
* `scripts/summarize_footer_header_manual_review.py`
* `training/footer_header_noise_report_only_package.md`

Current scope:

* format `pdf` only
* label `footer_header_noise` only
* report-only
* no expected mutation
* no `samples/check_quality.sh` behavior change

Current `smoke20_v2` readout:

* capability status: `ready`
* selected rows: `20`
* rows with approved inputs processed: `19`
* skipped license rows: `1`
* bridge compatibility: `ready`
* legacy footer-header candidate rows: `135`
* matched legacy feature rows: `135`
* output feature rows: `135`
* predicted labels:
  * `footer_header_noise = 51`
  * `paragraph = 66`
  * `heading = 16`
  * `caption = 2`
* emitted hints: `12`
* no-override rows: `116`
* hard conflicts: `7`

Current `pdf_all_v2` readout:

* capability status: `ready`
* selected rows: `77`
* rows with approved inputs processed: `76`
* skipped license rows: `1`
* legacy footer-header candidate rows: `360`
* matched legacy feature rows: `360`
* output feature rows: `360`
* predicted labels:
  * `footer_header_noise = 53`
  * `heading = 167`
  * `paragraph = 109`
  * `table_like = 27`
  * `caption = 4`
* emitted hints: `12`
* no-override rows: `341`
* hard conflicts: `7`

Current `pdf_all_v3_footer_refined` readout:

* capability status: `ready`
* selected rows: `77`
* rows with approved inputs processed: `76`
* skipped license rows: `1`
* legacy footer-header candidate rows: `360`
* matched legacy feature rows: `360`
* output feature rows: `360`
* predicted labels unchanged from `pdf_all_v2`
* emitted hints: `6`
* no-override rows: `341`
* hard conflicts: `13`
* newly blocked reason:
  * `dense_edge_row_conflict = 6`

Current recommended report-only package:

* label: `footer_header_noise`
* profile: `conservative_v2`
* `model_confidence_threshold = 0.95`
* `cooperative_threshold = 0.85`
* emit label allowlist stays `footer_header_noise` only
* current tracked summary:
  * `training/footer_header_noise_report_only_package.md`
* current manual-review export:
  * `scripts/export_footer_header_manual_review.py`
  * `scripts/summarize_footer_header_manual_review.py`
  * local-only `footer_header_manual_review.tsv`
  * local-only `footer_header_manual_review.md`
  * local-only `footer_header_manual_review_summary.tsv`
  * local-only `footer_header_manual_review_summary.md`

What now works:

* find PDF rows from the external-quality manifest
* resolve local input files
* run the normal quality helper unchanged and keep its Markdown/metadata outputs
* export legacy block-level PDF candidates in a side channel
* bridge arbitrary external PDF block candidates into `baseline_v3`-compatible
  text-block features
* run offline `HGB` teacher predictions plus cooperative gate scoring in
  report-only mode

Current interpretation:

* the runner is now a true report-only teacher-hint dry run for
  `footer_header_noise`
* most candidate rows are still blocked because the teacher prefers
  `heading`/`paragraph`/`table_like`, not because the bridge is missing
* `pdf_all_v2` still allowed a small group of false-positive edge-row booking
  cells through as emitted hints
* `pdf_all_v3_footer_refined` adds a narrower guard for dense multi-column
  edge-row cells, removing those booking-row false positives without driving
  coverage to `0`
* central-body and sentence-like risk rows are being kept out of `emit` in the
  current pass
* `form_key_value` alone was not the right blocker, because the suspicious
  booking row also emitted non-`form_key_value` cells like `2`, `3`, and
  `12/26-12/31`
* the current remaining emit surface is only the isolated page-number-style
  shells from the small `md_test` variants
* based on the current `pdf_all_v3_footer_refined` slice, there is no obvious
  additional guard to add before a larger manual review
* the next step is therefore manual-review summarization, not gate expansion

## Candidate Questions

The dry run should answer:

* do `footer_header_noise` hints mainly agree with existing rules?
* do `heading` hints expose obvious future wins without broad regressions?
* do `keep_as_text` hints mostly land on references/footnotes rather than body?
* how many potential regressions are being avoided by `no_override`?

Current next evaluation checklist:

* reuse `conservative_v2` unchanged on a larger PDF slice
* export a manual-review package that includes emit, hard-conflict, and
  high-confidence `no_override` rows
* manually review all emitted hints first
* fill `reviewer_decision` / `reviewer_notes` inside
  `footer_header_manual_review.tsv`
* run `scripts/summarize_footer_header_manual_review.py`
* use the summary recommendation to decide `keep/refine/adjust/expand/pause`
* audit the `confidence<0.95` `footer_header_noise` rows separately
* keep `heading` / `keep_as_text` out of this runner expansion for now
* if review is clean, prepare a larger report-only benchmark
* if review is not clean, refine guards again without widening labels

Manual review contract:

* blank `reviewer_decision` rows are allowed and summarize as `blank`
* a fully blank package should return `waiting_for_manual_review`
* do not use an unreviewed package as justification for runtime work
* keep `heading` and `keep_as_text` paused until this footer/header review lane
  is complete

## Recommended First Labels

The first external-quality dry run should only include:

* `footer_header_noise`

Current package recommendation:

* only `footer_header_noise` should move into the next external-quality manual
  review stage
* `heading` and `keep_as_text` remain later report-only expansions
* this package still does not authorize runtime or convert-path work

Labels to evaluate later, but not yet enabled in this runner:

* `heading`
* `keep_as_text`

Still excluded:

* `paragraph`
* `list_item`
* `table_like`
* `caption`

## Runner Separation

If this plan is implemented later, it should use a dedicated runner or helper.

It should not reuse:

* normal product output mutation paths
* expected-update paths
* runtime model-loading paths

## Runtime Note

Even a successful external-quality dry run is still not runtime approval.

After a dry run, the project would still need:

* gated design review
* convert-hook proposal review
* speed/closure checks
* bench review
* explicit fail-closed review

The manual-review export exists precisely because a clean report-only slice is
still evidence gathering, not integration approval.

The manual-review summary exists because filled reviewer decisions, not dry-run
counts alone, are the gate for deciding whether to keep the profile unchanged,
refine guards, or expand the benchmark.
