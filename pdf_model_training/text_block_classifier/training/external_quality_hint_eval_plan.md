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

A future report-only runner would need:

* converted PDF block candidates from the normal product path
* block-level features compatible with the text-block teacher feature surface
* optional teacher predictions or distilled hint TSV
* source identity for each evaluated row

Optional inputs:

* adapter-like block rows for bbox/text alignment
* conflict summaries from deterministic rules

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

## Current v0 Scaffold Status

Current tracked runner:

* `scripts/run_external_quality_hint_dry_run.py`

Current scope:

* format `pdf` only
* label `footer_header_noise` only
* report-only
* no expected mutation
* no `samples/check_quality.sh` behavior change

Current `smoke20` readout:

* capability status: `partial`
* selected rows: `20`
* rows with approved inputs processed: `19`
* skipped license rows: `1`
* legacy footer-header candidate rows: `135`
* emitted hints: `0`
* no-override rows: `135`
* conflict-flagged candidate rows: `57`

What already works:

* find PDF rows from the external-quality manifest
* resolve local input files
* run the normal quality helper unchanged and keep its Markdown/metadata outputs
* export legacy block-level PDF candidates in a side channel

Current blocker:

* there is still no bridge from arbitrary external-quality PDF blocks into the
  `baseline_v3` / `HGB` teacher feature surface

Interpretation:

* the runner is useful today as a capability and risk-audit scaffold
* it is not yet a true teacher-hint dry run
* until the feature bridge exists, emitted model hints must remain `0`

## Candidate Questions

The dry run should answer:

* do `footer_header_noise` hints mainly agree with existing rules?
* do `heading` hints expose obvious future wins without broad regressions?
* do `keep_as_text` hints mostly land on references/footnotes rather than body?
* how many potential regressions are being avoided by `no_override`?

## Recommended First Labels

The first external-quality dry run should only include:

* `footer_header_noise`
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
