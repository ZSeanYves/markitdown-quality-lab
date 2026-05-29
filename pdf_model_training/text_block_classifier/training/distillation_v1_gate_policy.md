# PDF Text Block Distillation v1 Gate Policy

## Scope

Distillation v1 is still:

* offline only
* report only
* `Task A` only

Distillation v1 is not:

* runtime integration
* convert-layer behavior change
* parser/layout recovery
* a `Task B` boundary route

## Allowed Candidate Labels

v1 only allows these labels to enter the gated candidate set:

* `footer_header_noise`
* `heading`
* `keep_as_text`

## Blocked Labels

v1 does not allow override candidates for:

* `paragraph`
* `list_item`
* `table_like`
* `caption`

Interpretation:

* these labels may still be useful to the offline teacher
* they are not allowed to emit v1 gated hints
* `caption` remains deny-for-now until a specialist route improves the boundary

## Core v1 Principles

v1 hints remain:

* report-only
* fail-closed
* no-runtime
* no-override by default unless a narrow gate passes

Every v1 candidate must satisfy:

1. `HGB` confidence threshold
2. label-specific threshold
3. feature-level sanity guard
4. conflict detection
5. `no_override` fallback when any condition fails

## Global Threshold

Current default v1 threshold:

* confidence `>= 0.95`

Rationale:

* v0 at `0.95` already provides much stronger precision than `0.90`
* v1 is intentionally more conservative than v0
* v1 prioritizes clean external-quality dry-run candidates over coverage

## Label-Specific Policy

### `footer_header_noise`

May emit only when:

* predicted label is `footer_header_noise`
* confidence `>= 0.95`
* the block is near page top or near page bottom
* there is at least one header/footer-like support signal
  * `contains_page_hint`
  * `near_top`
  * `near_bottom`
  * top/bottom position bucket
* the text is not obviously long body content
* there is no clear heading/table/caption/list conflict

Blocking intent:

* do not override obvious body paragraphs
* do not convert heading-like or table-like rows into noise

### `heading`

May emit only when:

* predicted label is `heading`
* confidence `>= 0.95`
* heading-like shape support is present
  * `heading_like_short`
  * `isolated_heading_like`
  * `heading_like_gap_before`
  * `section_number_prefix`
  * `starts_with_section_word`
  * `title_case_short`
  * `all_caps_short`
* the block is not a very long paragraph
* the block is not table-like, form-like, caption-like, or list-like
* punctuation and marker conflicts are absent

Blocking intent:

* do not relabel long paragraphs
* do not relabel form/table rows
* do not trust heading predictions when list or caption signals conflict

### `keep_as_text`

May emit only when:

* predicted label is `keep_as_text`
* confidence `>= 0.95`
* there is footnote/reference/form-like or small-isolated support
  * `contains_form_hint`
  * `contains_page_hint`
  * near bottom position
  * short or isolated text shape
  * dense reference-like punctuation/digit pattern
* the block is not clearly heading-like, list-like, or table-like

Blocking intent:

* do not override clear headings
* do not override list items or table-like rows
* do not trust broad paragraph-like spans without auxiliary support

## Conflict Detection

v1 should block when the predicted label conflicts with strong evidence:

* `footer_header_noise` blocked by:
  * long paragraph-like text
  * explicit table/caption/list cues
* `heading` blocked by:
  * terminal sentence punctuation plus long text
  * table/form/caption cues
  * list-marker cues
* `keep_as_text` blocked by:
  * heading-like compact title shape
  * table/form/list cues that suggest another route

## Output Policy

For every input row, v1 must emit one of:

* `emit`
* `blocked_label_not_allowed`
* `blocked_low_confidence`
* `blocked_sanity_guard`
* `blocked_conflict`
* `no_override`

Interpretation:

* `emit` means “candidate for future external-quality dry run”
* every other status means “keep rules / no override”

## Current v1 Objective

v1 is trying to answer only one question:

* can `footer_header_noise`, `heading`, and `keep_as_text` be reduced into
  narrow report-only gated hints that are safer than v0?

v1 is not trying to solve:

* broad paragraph coverage
* list-item routing
* table-like routing
* caption routing

## Future Runtime Note

Even if v1 looks promising:

* do not hook it into `convert/pdf`
* do not change product output
* do not change `expected`
* do not present it as runtime-ready

The next step after v1, if results are strong enough, is:

* external-quality report-only dry run

Only after that could a future gated design be proposed, and that would still
be separate from runtime implementation.

## Cooperative Gate Note

v1 is still a threshold-plus-guard surface.

It does not yet model:

* explicit rule support weighting
* explicit context sanity weighting
* explicit conflict penalties
* cooperative scoring against existing PDF rule evidence

Those pieces move into the next report-only stage:

* `rule_model_cooperative_gate_policy.md`
* `scripts/evaluate_rule_model_cooperative_gate.py`
