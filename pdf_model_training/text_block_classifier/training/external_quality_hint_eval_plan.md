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
* emitted hints remain narrow and mostly page-number / schedule-shell style
  rows
* central-body and sentence-like risk rows are being kept out of `emit` in the
  current pass

## Candidate Questions

The dry run should answer:

* do `footer_header_noise` hints mainly agree with existing rules?
* do `heading` hints expose obvious future wins without broad regressions?
* do `keep_as_text` hints mostly land on references/footnotes rather than body?
* how many potential regressions are being avoided by `no_override`?

## Recommended First Labels

The first external-quality dry run should only include:

* `footer_header_noise`

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
