# PDF Text Block Distillation Policy

This policy defines how `text_block_classifier` can move from rich offline
teacher training to future, tightly constrained runtime hints.

## Current Teacher Status

* current primary offline teacher: `HistGradientBoostingClassifier`
* best current gold result:
  * `DocLayNet pilot3000_v1 baseline_v3`
  * heldout macro F1 = `0.8097`
  * heldout accuracy = `0.8269`
* teacher is local-only and offline-only
* teacher is not a convert/runtime dependency

Current interpretation:

* the `HGB` teacher route is strong enough to justify distillation work
* the historical logistic baseline is still useful for lightweight comparison,
  but it is not the current quality ceiling
* `caption` remains the weakest major label and should not be treated as solved

## Distillation Goals

Teacher outputs are only useful if they can be reduced into runtime-safe forms.
The preferred distillation targets are:

1. high-confidence hints
2. rule suggestions for obvious buckets
3. compact decision tables and thresholds
4. small auxiliary model candidates only if size/speed/closure stay controlled

The intended priority is:

1. deterministic rules remain primary
2. distilled hints may assist rules
3. compact model candidates are optional and must fail closed

## What We Are Distilling

The current teacher is strongest on:

* `footer_header_noise`
* `table_like`
* `heading`
* `paragraph`
* `list_item`

The current teacher is weaker on:

* `caption`
* patent/legal short numbered lines
* affiliation/address lines
* form-like short rows
* table/caption boundary cases

This means the first distillation targets should be:

* strong `footer_header_noise` hints
* strong `table_like` hints
* strong `heading` hints
* high-confidence `paragraph` / `list_item` hints when the marker and geometry
  signals agree

`caption` should remain conservative until a specialist path improves that
boundary.

## Fail-Closed Policy

Distillation must fail closed.

Required behavior:

* low confidence -> no override
* conflicting signal -> no override
* unsupported layout family -> no override
* specialist disagreement -> no override unless the specialist is explicitly
  trusted for that narrow boundary
* unseen or weakly supervised source -> no gold-style override

Runtime-oriented distilled outputs should prefer:

* abstain / keep rules
* `unknown`
* `uncertain`
* label-specific “hint only” behavior

They should not silently relabel broad page content without confidence and
agreement checks.

## Confidence Gating Direction

Current `pilot3000_v1` HGB heldout audit shows:

* confidence `>= 0.80`:
  * coverage `0.6955`
  * covered macro F1 `0.9153`
* confidence `>= 0.90`:
  * coverage `0.5601`
  * covered macro F1 `0.9457`
* confidence `>= 0.95`:
  * coverage `0.4289`
  * covered macro F1 `0.9649`

Current labels with the clearest fail-closed potential:

* at `>= 0.90`: `footer_header_noise`, `list_item`, `paragraph`
* at `>= 0.95`: `footer_header_noise`, `heading`, `keep_as_text`,
  `list_item`, `paragraph`

Current caution:

* `caption` improves with confidence but still needs specialist support before
  it should be trusted as a broad override class
* `table_like` is strong, but table/caption boundary handling still benefits
  from a dedicated specialist path

## Feature Families Most Worth Distilling

The current HGB teacher relies most on:

* bbox / geometry
* text lexical ratios and punctuation shape
* list marker / section prefix families
* page position
* caption cue families
* some neighbor context and alignment

Most promising direct rule candidates:

* header/footer position plus low-text-density cues
* numbered/list-marker patterns
* short heading-like text without terminal punctuation
* strong table-like geometry plus tabular text hints

Less suitable for direct naive rules:

* caption-only overrides
* patent/legal boundary cases
* address / affiliation / key-value short rows

These should stay teacher-driven or specialist-driven until more evidence is
available.

## Specialist Data Policy

`PubTables-1M` is a specialist source, not a replacement gold source.

Allowed role:

* `table_like` specialist
* optional weak `caption` probe

Required restrictions:

* never mix `PubTables` rows into `DocLayNet` gold heldout
* never present `PubTables`-assisted results as pure `DocLayNet` gold results
* keep source identity explicit in every mixed experiment

`PubLayNet` policy remains:

* weak supplement only
* never use as gold eval

## Runtime Preconditions

Even if distillation looks promising, no convert/runtime proposal should be made
before the following gates are passed:

1. `DocLayNet` heldout remains stable after distillation
2. external PDF quality evaluation shows net benefit
3. `bash samples/check.sh`
4. `bash samples/check_quality.sh --format pdf`
5. `bash samples/bench.sh`
6. speed regression stays within an agreed threshold
7. binary/closure size remains acceptable
8. failure modes remain fail-closed

Only after these gates should a rule-gated convert-layer integration even be
proposed.

## Explicitly Out Of Scope This Round

Not allowed this round:

* runtime integration
* convert-layer rewiring
* direct use of heavy teacher checkpoints in CLI/runtime
* PDF OCR as the main route
* replacing deterministic rules with a model-first path
* committing large models or real dataset bytes

## Near-Term Distillation Plan

1. keep `HGB` as the primary offline teacher
2. finish teacher audits and error buckets
3. add a `PubTables` specialist adapter scaffold
4. run a tiny specialist smoke without polluting gold eval
5. train a narrow specialist only under local-only conditions
6. test specialist + teacher gating on the table/caption boundary
7. convert the strongest evidence into:
   * confidence thresholds
   * rule candidates
   * abstain conditions
   * compact candidate representations

## Distillation v0: High-Confidence Hint Export

The first concrete distillation artifact is a local-only hint export from the
`pilot3000_v1 baseline_v3 HGB` teacher.

Current export script:

* `scripts/export_hgb_distilled_hints.py`

Current output schema:

* `sample_id`
* `split`
* `source_page_id`
* `source_region_id`
* `page_no`
* `bbox`
* `text`
* `gold_label`
* `predicted_label`
* `confidence`
* `threshold`
* `hint_label`
* `hint_action`
* `hint_status`
* `reason`

Current policy:

* allowed labels:
  * `footer_header_noise`
  * `heading`
  * `keep_as_text`
  * `list_item`
  * `paragraph`
  * `table_like`
* deny labels:
  * `caption`
* `gold_label` is used only for offline evaluation, never for hint emission
* low-confidence or denied predictions remain `no_override`

Current `heldout` v0 results:

* threshold `>= 0.90`
  * coverage `0.5491`
  * emitted accuracy `0.9561`
  * fail-closed heldout macro F1 `0.6442`
  * wrong emitted count `268`
* threshold `>= 0.95`
  * coverage `0.4204`
  * emitted accuracy `0.9737`
  * fail-closed heldout macro F1 `0.5845`
  * wrong emitted count `123`

Current label interpretation:

* `footer_header_noise`
  * ready for rule-hint exploration
* `heading`
  * ready for rule-hint exploration
* `keep_as_text`
  * ready for rule-hint exploration
* `list_item`
  * keep teacher-only for now
* `paragraph`
  * keep teacher-only for now
* `table_like`
  * keep teacher-only for now
* `caption`
  * deny for now

Interpretation note:

* these v0 metrics score the whole heldout split under fail-closed abstention,
  not just the covered slice
* this is intentionally stricter than the earlier confidence-gating audit, which
  only described the quality of the covered subset

Important caution:

* v0 is still local-only and offline-only
* v0 does not authorize convert/runtime integration
* v0 only justifies the next design step:
  * rule-gated hint planning
  * specialist-backed boundary experiments
  * fail-closed routing design

## Boundary Scope Clarification

This policy is only for convert-layer text block semantics.

In scope:

* `paragraph`
* `heading`
* `footer_header_noise`
* `caption`
* `table_like`
* `list_item`
* `keep_as_text`

Out of scope:

* reading order
* cross-page merge / no-merge
* column detection
* parser-side region recovery
* multi-column parser risk

Interpretation:

* `text_block_classifier` distillation is `Task A` plus `Task C`
* `layout_recovery_model` remains `Task B`
* old mixed `pdf_layout_classifier` manifests and legacy boundary labels must
  not be reintroduced into current text-block distillation
* legacy `pdf_layout_linear_*` metadata and report-only local eval presets are
  compatibility artifacts, not distillation candidates

## Distillation v1: Label-Specific Gated Hints

Distillation v1 tightens v0 further.

Scope:

* still offline-only
* still report-only
* still `Task A` only

Allowed v1 labels:

* `footer_header_noise`
* `heading`
* `keep_as_text`

Still blocked in v1:

* `paragraph`
* `list_item`
* `table_like`
* `caption`

Required v1 gate conditions:

1. confidence `>= 0.95`
2. label-specific sanity guard
3. conflict detection
4. `no_override` fallback when any guard fails

Current v1 artifact:

* `scripts/evaluate_distillation_v1_gates.py`
* `training/distillation_v1_gate_policy.md`

Current v1 heldout goal:

* reduce candidate coverage further than v0
* keep or improve emitted precision
* identify which labels are safe enough for a future external-quality dry run

Current `pilot3000_v1` heldout v1 result at `0.95`:

* total rows: `11123`
* v0 emitted rows: `4676`
* v1 emitted rows: `1219`
* v1 coverage: `0.1096`
* v1 emitted accuracy: `0.9779`
* v1 emitted macro F1: `0.2648`

Current v1 interpretation:

* `footer_header_noise`
  * ready for external-quality dry-run planning
  * precision `0.9975`, recall `0.5770`, F1 `0.7311`
* `heading`
  * still needs more guard work
  * precision `0.9670`, recall `0.4099`, F1 `0.5758`
* `keep_as_text`
  * still needs more guard work
  * precision `0.9778`, recall `0.3793`, F1 `0.5466`

Current v1 warning:

* the main residual wrong-emitted pair is still `paragraph -> heading`
* `caption` remains denied
* `paragraph`, `list_item`, and `table_like` remain outside the v1 gated set

## Cooperative Gate Direction

The next stage after v1 is not runtime hookup.

It is a report-only cooperative gate that combines:

* model confidence
* rule support
* context sanity
* conflict penalties
* label-risk penalties

Important interpretation:

* rules stay primary
* hard conflicts still block regardless of model confidence
* the model is only allowed to reinforce rule-compatible candidates
* this inherits the old fail-closed / reason-tag / no-override discipline
  without inheriting the old mixed block/layout scope

Current v1 runtime note:

* v1 still does not authorize convert/runtime integration
* the only next step after v1 is a report-only external-quality dry run
* the tracked external-quality package should stay `footer_header_noise` only

## Cooperative Gate v0 Readout

The first cooperative gate pass is still local-only and report-only.

Evaluator:

* `scripts/evaluate_rule_model_cooperative_gate.py`

Input policy:

* allowed labels remain only:
  * `footer_header_noise`
  * `heading`
  * `keep_as_text`
* hard conflicts still beat model confidence
* `paragraph`, `list_item`, `table_like`, and `caption` remain outside the
  cooperative emit surface

Current `pilot3000_v1` heldout comparison:

* v1 baseline:
  * emitted rows `1219`
  * coverage `0.1096`
  * emitted accuracy `0.9779`
* cooperative `conservative @ 0.85`:
  * emitted rows `698`
  * coverage `0.0628`
  * emitted accuracy `0.9957`
  * wrong emitted `3`
* cooperative `balanced @ 0.85`:
  * emitted rows `297`
  * coverage `0.0267`
  * emitted accuracy `1.0000`
  * wrong emitted `0`
* cooperative `model_heavy @ 0.80`:
  * emitted rows `342`
  * coverage `0.0307`
  * emitted accuracy `1.0000`
  * wrong emitted `0`

Interpretation:

* the cooperative gate succeeds when judged as a rule-preserving filter
* it meaningfully reduces wrong emitted cases relative to raw v1
* the best current tradeoff is `conservative @ 0.85`
* `balanced` and `model_heavy` become too sparse under the current hard
  conflicts to justify as the first dry-run surface

Current label interpretation after cooperative filtering:

* `footer_header_noise`
  * still the clearest external-quality report-only candidate
  * current recommended package profile is `conservative_v2`
  * current next step is larger/manual external-quality review, not runtime
* `heading`
  * still needs more guard refinement because the remaining residual risk is
    mostly paragraph-like content
* `keep_as_text`
  * remains too sparse under current guards and should stay report-only

Important note:

* these cooperative results still do not authorize runtime integration
* they only justify the next report-only step:
  * external-quality manual review for `footer_header_noise`
  * more guard refinement for `heading`
  * more guard refinement for `keep_as_text`
* `paragraph`, `list_item`, `table_like`, and `caption` remain outside this
  package
