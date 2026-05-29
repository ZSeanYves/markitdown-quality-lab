# Rule-Model Cooperative Gate Policy

## Goal

This policy defines a report-only cooperative gate for future
`text_block_classifier` distillation work.

It is intentionally:

* offline-only
* report-only
* fail-closed
* `Task A` only

It is not:

* runtime integration
* a convert-layer behavior change
* a parser/layout recovery route

## Core Principle

The rule system remains primary.

Interpretation:

* hard rule conflicts beat model confidence
* the model may only assist when rule evidence and context sanity agree
* the cooperative gate must prefer `no_override` whenever rule evidence is
  weak or conflict is strong

This preserves the spirit of the older conservative gate work:

* reason-tag driven
* fail-closed
* narrow overrides only

But it does not inherit the old mixed block/layout scope.

## Allowed Labels

Current cooperative gate labels:

* `footer_header_noise`
* `heading`
* `keep_as_text`

Still excluded:

* `paragraph`
* `list_item`
* `table_like`
* `caption`

## Scoring Components

Every candidate is evaluated with:

* `model_confidence_score`
* `rule_support_score`
* `context_sanity_score`
* `conflict_penalty_score`
* `label_risk_penalty`

Recommended formula:

```text
cooperative_score =
  w_model * model_confidence
+ w_rule * rule_support
+ w_context * context_sanity
- w_conflict * conflict_penalty
- w_label_risk * label_risk
```

The formula only applies after:

* allowed-label check
* minimum model-confidence check
* hard-conflict check

## Initial Weights

### Conservative

* `footer_header_noise`
  * `w_model = 0.35`
  * `w_rule = 0.40`
  * `w_context = 0.20`
  * `w_conflict = 1.00`
  * `w_label_risk = 0.05`
* `heading`
  * `w_model = 0.30`
  * `w_rule = 0.35`
  * `w_context = 0.25`
  * `w_conflict = 1.00`
  * `w_label_risk = 0.10`
* `keep_as_text`
  * `w_model = 0.35`
  * `w_rule = 0.30`
  * `w_context = 0.25`
  * `w_conflict = 1.00`
  * `w_label_risk = 0.10`

### Balanced

* `footer_header_noise`
  * `w_model = 0.40`
  * `w_rule = 0.32`
  * `w_context = 0.18`
  * `w_conflict = 0.95`
  * `w_label_risk = 0.05`
* `heading`
  * `w_model = 0.38`
  * `w_rule = 0.30`
  * `w_context = 0.20`
  * `w_conflict = 0.95`
  * `w_label_risk = 0.12`
* `keep_as_text`
  * `w_model = 0.40`
  * `w_rule = 0.25`
  * `w_context = 0.20`
  * `w_conflict = 0.95`
  * `w_label_risk = 0.12`

### Model Heavy

* `footer_header_noise`
  * `w_model = 0.55`
  * `w_rule = 0.20`
  * `w_context = 0.10`
  * `w_conflict = 0.85`
  * `w_label_risk = 0.05`
* `heading`
  * `w_model = 0.52`
  * `w_rule = 0.18`
  * `w_context = 0.15`
  * `w_conflict = 0.85`
  * `w_label_risk = 0.15`
* `keep_as_text`
  * `w_model = 0.55`
  * `w_rule = 0.15`
  * `w_context = 0.10`
  * `w_conflict = 0.85`
  * `w_label_risk = 0.15`

## Initial Thresholds

Global default:

* `model confidence >= 0.95`

Initial cooperative score thresholds to compare:

* `0.80`
* `0.85`
* `0.90`

Suggested first default for a future dry run:

* conservative profile
* `cooperative_score >= 0.85`

## Hard Conflicts

Hard conflicts must block regardless of score.

### `footer_header_noise`

Hard conflicts:

* long paragraph-like body content
* central dense paragraph region
* table/caption/list conflict
* strong compact heading shape conflict

### `heading`

Hard conflicts:

* long paragraph conflict
* table/form conflict
* list conflict
* terminal period / sentence-like conflict
* caption conflict

### `keep_as_text`

Hard conflicts:

* clear heading conflict
* clear list conflict
* clear table conflict
* paragraph-like long sentence conflict without supporting reference/form cues

## Rule Support Mapping

### `footer_header_noise`

Useful rule support proxies:

* `near_top`
* `near_bottom`
* edge-position buckets
* `contains_page_hint`
* compact height / edge-ish geometry

### `heading`

Useful rule support proxies:

* `heading_like_short`
* `section_number_prefix`
* `starts_with_section_word`
* `title_case_short`
* `all_caps_short`
* heading-like gap / isolation

### `keep_as_text`

Useful rule support proxies:

* `contains_form_hint`
* `contains_page_hint`
* near-bottom position
* short isolated shape
* reference-like punctuation/digit density

## Output Actions

Current actions:

* `emit_hint`
* `no_override`
* `report_only_conflict`

Interpretation:

* `emit_hint` means “candidate for a future report-only dry run”
* `report_only_conflict` means “the model and rules disagree enough that the
  row should be surfaced for audit, not override”
* `no_override` means “keep rules only”

## External-Quality Status

Current tracked runner:

* `scripts/run_external_quality_hint_dry_run.py`

Current enabled label:

* `footer_header_noise`

Current bridge/runtime boundary:

* report-only only
* offline `HGB` teacher only
* no runtime hook
* no convert-path mutation

Current `smoke20_v2` result under:

* conservative profile
* `model_confidence >= 0.95`
* `cooperative_score >= 0.85`

Observed outcome:

* capability status: `ready`
* bridge compatibility: `ready`
* candidate rows: `135`
* emitted hints: `12`
* blocked hard conflicts: `7`
* dominant blocked reasons:
  * `label_not_allowed:paragraph`
  * `confidence<0.95`
  * `label_not_allowed:heading`

Current `pdf_all_v2` result under the same profile:

* capability status: `ready`
* candidate rows: `360`
* emitted hints: `12`
* blocked hard conflicts: `7`
* dominant blocked reasons:
  * `label_not_allowed:heading`
  * `label_not_allowed:paragraph`
  * `confidence<0.95`
  * `label_not_allowed:table_like`

Refined `pdf_all_v3_footer_refined` result under:

* `conservative_v2`
* same `model_confidence >= 0.95`
* same `cooperative_score >= 0.85`

Observed outcome:

* capability status: `ready`
* candidate rows: `360`
* emitted hints: `6`
* blocked hard conflicts: `13`
* new blocked reason:
  * `dense_edge_row_conflict = 6`

Refinement intent:

* keep `conservative` unchanged
* add a narrower `footer_header_noise` guard only in `conservative_v2`
* block dense multi-column edge-row cells that look like schedule/table rows,
  not isolated page-number shells

Interpretation:

* the cooperative gate is no longer blocked on feature compatibility
* the current conservative pass is still narrow by design
* most non-emits are caused by teacher label disagreement, not cooperative
  score failure
* central-body and sentence-like body-risk rows are being retained as
  `no_override` rather than leaking into `emit`
* `form_key_value` should not be treated as a blanket hard conflict:
  the stronger external-quality failure mode was dense edge-row structure, and
  that row included both `form_key_value` and non-`form_key_value` cells

## Runtime Note

This policy is not a runtime approval.

If a future integration is ever proposed, the model side must be consumed only
as:

* reason-tag-compatible hints
* fail-closed assist signals
* reversible, narrow evidence

It must not:

* replace the deterministic rules
* override hard rule conflicts
* reactivate the old mixed block/layout route

## Initial Heldout Readout

Current local-only evaluator:

* `scripts/evaluate_rule_model_cooperative_gate.py`

Current `pilot3000_v1` heldout comparison:

### Conservative

* threshold `>= 0.80`
  * emitted rows `1043`
  * coverage `0.0938`
  * emitted accuracy `0.9789`
  * wrong emitted `22`
* threshold `>= 0.85`
  * emitted rows `698`
  * coverage `0.0628`
  * emitted accuracy `0.9957`
  * wrong emitted `3`
* threshold `>= 0.90`
  * emitted rows `297`
  * coverage `0.0267`
  * emitted accuracy `1.0000`
  * wrong emitted `0`

### Balanced

* threshold `>= 0.80`
  * emitted rows `1041`
  * coverage `0.0936`
  * emitted accuracy `0.9789`
  * wrong emitted `22`
* threshold `>= 0.85`
  * emitted rows `297`
  * coverage `0.0267`
  * emitted accuracy `1.0000`
  * wrong emitted `0`
* threshold `>= 0.90`
  * emitted rows `0`

### Model Heavy

* threshold `>= 0.80`
  * emitted rows `342`
  * coverage `0.0307`
  * emitted accuracy `1.0000`
  * wrong emitted `0`
* threshold `>= 0.85`
  * emitted rows `0`
* threshold `>= 0.90`
  * emitted rows `0`

Interpretation:

* `conservative @ 0.85` is the best first v1.5/v2 candidate
* it improves over raw v1 by reducing wrong emitted from `27` to `3`
  while keeping usable `footer_header_noise` coverage
* `balanced` is viable but collapses `heading` too aggressively at `0.85`
* `model_heavy` does not actually buy useful coverage under the current hard
  conflicts and thresholds, so it is not recommended

Current label outcome:

* `footer_header_noise`
  * best cooperative dry-run candidate
* `heading`
  * still blocked by paragraph/list/caption conflicts often enough that it
    should stay report-only until more guard refinement lands
* `keep_as_text`
  * still too sparse under current cooperative rules and should stay
    report-only

## External Quality Dry-Run Note

The first external-quality runner now exists as a tracked scaffold:

* `scripts/run_external_quality_hint_dry_run.py`

Current interpretation:

* it can reuse the normal PDF quality path unchanged
* it can collect report-only Markdown/metadata outputs
* it can export legacy block candidates for `footer_header_noise` auditing
* it still cannot emit real cooperative hints because arbitrary external PDF
  blocks do not yet have a teacher-compatible `baseline_v3` feature bridge

So the current external-quality state is:

* useful for capability checking
* useful for conflict/risk review
* not yet a real cooperative-hint evaluation surface
