# PDF Gate And Model Boundary Audit

## Summary

Current conclusion:

* historical PDF model and gate work did mix convert-layer block semantics and
  parser/layout boundary tasks
* the main mixed route was the old `pdf_layout_classifier` training spike and
  its related manifests, model metadata, debug manifests, and path fallbacks
* the newer split between `text_block_classifier/` and
  `layout_recovery_model/` is directionally correct, but some legacy files,
  names, and debug surfaces still blur the boundary
* the current `HGB` teacher and distillation v0 should be treated as
  `Task A` and `Task C` only
* cross-page merge, reading order, and parser-side region recovery should stay
  isolated as `Task B`

This audit does not propose runtime integration. It only defines boundaries,
legacy status, and a cleanup plan.

Status update:

* PR 1 boundary cleanup has now split the main-repo debug eval manifest into
  explicit block-assist and boundary-assist surfaces while keeping the old
  mixed manifest for compatibility
* PR 1 also marks legacy tracked JSON model metadata and compatibility scripts
  more explicitly as historical surfaces

## Discovered Legacy Routes

### Main historical mixed route

Legacy route identity:

* naming:
  * `pdf_layout_classifier`
  * `.external/layout_model`
  * `samples/pdf_layout_classifier`
* tracked model metadata:
  * `text_block_classifier/models/pdf_layout_linear_*.json`
  * `text_block_classifier/models/round*.json`
* legacy manifests:
  * `text_block_classifier/archive/old_manifests/manifest.legacy.mixed.tsv`
  * `text_block_classifier/archive/old_manifests/manifest.example.legacy.tsv`
* legacy labels:
  * `text_block_classifier/archive/repo_manual_labels/*.tsv`
* legacy note:
  * `text_block_classifier/archive/legacy_samples_notice.md`

Why it is mixed:

* model task names still say `pdf_layout_classifier` even when labels are block
  semantics
* manifests contain `record_kind=block`, `record_kind=boundary`, and even
  `record_kind=all`
* historical block models include `boundary_*` features in the same feature
  vector
* debug eval manifests mix heading/caption/body rows with cross-page merge rows

### Current split route

Current intended split:

* `text_block_classifier/` for convert-layer block semantics
* `layout_recovery_model/` for parser/layout recovery
* distillation and gating as a separate policy layer, not a third classifier

This split is already described correctly in:

* `text_block_classifier/README.md`
* `text_block_classifier/labels/label_schema.md`
* `layout_recovery_model/README.md`
* `layout_recovery_model/labels/label_schema.md`

## Task Boundary Table

| Task | Layer | Purpose | Typical Labels / Outputs | Must Not Do |
| --- | --- | --- | --- | --- |
| `Task A` text block classifier | `convert/pdf` | classify PDF text blocks into convert-layer semantics | `paragraph`, `heading`, `footer_header_noise`, `caption`, `table_like`, `list_item`, `keep_as_text` | decide reading order, cross-page merge, parser region recovery |
| `Task B` layout recovery model | `doc_parse/pdf/text`, parser/layout bridge | recover parser/layout structure and boundary risk | `reading_order`, `column_region`, `table_region`, `figure_region`, `caption_region`, `cross_page_merge`, `cross_page_no_merge`, `multi_column_risk` | assign final Markdown block semantics like `paragraph` or `heading` |
| `Task C` gate / runtime policy | future convert gate, future parser gate, debug/report policy | fail-closed gating, thresholds, abstain policy, reason/evidence surfaces | `no_override`, confidence threshold, reason tags, hint routing | become the classifier itself or silently override broad content |

## File Ownership Table

### Main repo runtime / parser / debug files

| File | Task | Status | Notes |
| --- | --- | --- | --- |
| `convert/pdf/pdf_classify.mbt` | `Task A` | `safe_to_keep` | narrow heuristic block classifier |
| `convert/pdf/pdf_heading_decision.mbt` | `Task A` + `Task C` | `safe_to_keep` | has reason tags and hard guards suited for future hint consumption |
| `convert/pdf/pdf_noise_decision.mbt` | `Task A` + `Task C` | `safe_to_keep` | same pattern as heading |
| `convert/pdf/pdf_layout_gate.mbt` | `Task C` | `safe_to_keep` | current narrow gated runtime surface |
| `convert/pdf/pdf_merge_decision.mbt` | `Task B` + `Task C` | `safe_to_keep` | boundary policy for cross-page merge; must stay separate from block classifier hints |
| `convert/pdf/pdf_layout_features.mbt` | `mixed_task` | `needs_split` | exports block features and boundary features under one `layout` surface |
| `doc_parse/pdf/api/pdf_api.mbt` | `Task B` | `safe_to_keep` | already states parser-facing output and higher-layer semantic separation |
| `doc_parse/pdf/layout_model_tool/main.mbt` | `mixed_layer` | `needs_split` | one tool handles `record-kind block|boundary` under old `layout_model_tool` name |
| `convert/pdf_debug/pdf_layout_assist.mbt` | `mixed_layer` | `document_only` | report-only provider abstraction; label suggestions are block-like but packaged as `layout_assist` |
| `debug/debug_app.mbt` | `mixed_layer` | `document_only` | layout-assist eval currently loads mixed manifests |
| `debug/testdata/layout_assist_eval/manifest.tsv` | `mixed_task` | `needs_split` | mixes block samples and boundary samples in one eval manifest |

### Quality-lab current active routes

| File / Dir | Task | Status | Notes |
| --- | --- | --- | --- |
| `text_block_classifier/README.md` | `Task A` | `keep` | correct current ownership statement |
| `text_block_classifier/labels/label_schema.md` | `Task A` | `keep` | correctly excludes parser/layout labels |
| `text_block_classifier/training/distillation_policy.md` | `Task C` | `keep` | current text block distillation policy |
| `text_block_classifier/training/roadmap.md` | `Task A` + `Task C` | `keep` | current roadmap for teacher, specialist, distillation |
| `text_block_classifier/scripts/export_hgb_distilled_hints.py` | `Task C` | `keep` | offline hint export only |
| `layout_recovery_model/README.md` | `Task B` | `keep` | correct ownership statement |
| `layout_recovery_model/labels/label_schema.md` | `Task B` | `keep` | parser/layout targets only |
| `dataset/dataset_registry.tsv` in both trees | `Task A` / `Task B` | `keep` | split dataset ownership is good |

### Legacy files inside `text_block_classifier`

| File / Dir | Task | Status | Notes |
| --- | --- | --- | --- |
| `text_block_classifier/models/pdf_layout_linear_*.json` | `mixed_task` | `archive_legacy` | block labels under `pdf_layout_classifier` task name and boundary-heavy features |
| `text_block_classifier/models/round*.json` | `mixed_task` | `archive_legacy` | same issue |
| `text_block_classifier/archive/old_manifests/manifest.legacy.mixed.tsv` | `mixed_task` | `archive_legacy` | direct mixed block/boundary manifest |
| `text_block_classifier/archive/old_manifests/manifest.example.legacy.tsv` | `mixed_task` | `archive_legacy` | task/layer columns expose the old mixed route |
| `text_block_classifier/archive/repo_manual_labels/*.tsv` | `mixed_task` | `archive_legacy` | contains both block and boundary manual labels |
| `text_block_classifier/archive/legacy_samples_notice.md` | `mixed_layer` | `keep` | useful historical explanation, but should be treated as legacy only |
| `text_block_classifier/scripts/path_roots.py` | `mixed_layer` | `needs_split` | still contains `pdf_layout_classifier` and `.external/layout_model` fallbacks |
| `text_block_classifier/scripts/train.py` | `mixed_layer` | `document_only` | legacy linear training spike that still understands mixed row identity |
| `text_block_classifier/scripts/local_eval.py` | `mixed_layer` | `archive_legacy` | report-only gate experiments tied to old mixed route |

## Concrete Confusion Points

### 1. Name confusion

Old names still collapse multiple things into “layout”:

* `pdf_layout_classifier`
* `layout_model_tool`
* `layout_assist`
* `.external/layout_model`

But these names have historically referred to both:

* block-semantic classification
* boundary merge / column / parser-layout signals

### 2. Manifest confusion

Mixed manifests explicitly contain:

* `record_kind=block`
* `record_kind=boundary`
* `record_kind=all`

This makes a single manifest look like one train/eval surface, even though it
actually spans `Task A` and `Task B`.

### 3. Feature confusion

Historical block models include `boundary_*` features such as:

* `boundary_prev_no_sentence_end`
* `boundary_next_starts_lowercase`
* `boundary_table_guard`
* `boundary_layout_compatible`

That does not automatically make them invalid, but it does blur whether the
model is learning:

* block semantics
* page-boundary continuation risk
* parser-layout transition cues

### 4. Debug/eval confusion

`debug/testdata/layout_assist_eval/manifest.tsv` still mixes:

* heading/body/caption/header-footer block rows
* `pdf_cross_page_paragraph` boundary row

This encourages “one assist summary for everything”, which is convenient for
debugging but bad for architectural clarity.

## Relationship To HGB Distillation v0

Current `HGB` distillation v0 is not the same as the old mixed route.

What it is:

* `Task A` teacher quality work on `DocLayNet`
* `Task C` fail-closed hint export and threshold audit

What it is not:

* parser/layout recovery
* cross-page merge prediction
* column detection
* runtime activation

Important alignment rule:

* current `text_block_classifier` distillation must not inherit old
  `boundary` labels or mixed manifests
* old `layout classifier` evidence may still inspire guard ideas, but should
  not define the scope of current text-block distillation

## Reuse vs Isolation

### Safe to reuse

These ideas remain useful:

* fail-closed reasoning
* explicit reason/evidence tags
* conservative gating over broad relabeling
* heldout-first evaluation discipline
* explicit distinction between `emit` and `no_override`

These structures are already good runtime-facing patterns:

* `PdfHeadingDecision.reason_tags`
* `PdfNoiseDecision.reason_tags`
* `PdfMergeDecision.reason_tags`
* `PdfLayoutGateDecision.override_allowed`
* `PdfLayoutGateDecision.override_blocked_reason`

### Must isolate

These should stay isolated from current text-block distillation:

* cross-page merge labels
* column-boundary labels
* parser-side region labels
* mixed manifests
* mixed debug manifests
* legacy `.external/layout_model` naming and model lookup paths

### Should be archived or downgraded to historical reference

* old linear JSON model metadata under `text_block_classifier/models/`
* `archive/old_manifests/*`
* `archive/repo_manual_labels/*`
* legacy local eval presets and reports tied to the mixed route

## Future Runtime Hook Draft

This section is a boundary sketch only. It is not an implementation request.

### Future `Task A` safe hook

If convert-layer hints are ever proposed, the narrowest safe place is:

* a future convert-layer block hint provider
* consumed only by block-semantic decision helpers such as:
  * heading demotion/promotion
  * noise demotion
  * narrow list-item suppression

That future surface should look like:

* `pdf_block_hint_provider`
* `pdf_block_hint_gate`
* optional `pdf_block_hint_model`

Required properties:

* fail closed
* no runtime dependency on Python artifacts
* no broad paragraph relabeling by default
* explicit abstain path
* explicit reason tags

### Future `Task B` safe hook

If parser/layout hints are ever proposed, they should be a separate provider
family under parser/layout ownership, for example:

* `pdf_layout_hint_provider`

That path would own:

* reading-order help
* column/region risk
* cross-page merge/no-merge hints

It must not share the same manifest, checkpoint, or consumption policy as
convert-layer block hints.

### Places that should not consume text-block hints

Do not use `Task A` distilled hints to directly drive:

* `doc_parse/pdf/api` extraction semantics
* cross-page merge decisions
* parser reading-order recovery
* region/column recovery

## Cleanup Plan

### Phase 1: document the boundary

Done by this audit:

* define `Task A`, `Task B`, `Task C`
* document that old `pdf_layout_classifier` was mixed
* document that current `HGB` distillation is `Task A` + `Task C` only

### Phase 2: isolate legacy references

Recommended next cleanup:

* mark old `pdf_layout_linear_*.json` and `round*.json` as legacy reference
  metadata only
* stop any default path fallback from preferring
  `samples/pdf_layout_classifier/` or `.external/layout_model/`
* keep mixed old manifests only under `archive/`

### Phase 3: split debug/eval surfaces

Recommended follow-up:

* split `debug/testdata/layout_assist_eval/manifest.tsv` into:
  * block-assist eval
  * boundary-assist eval
* rename report surfaces so “layout assist” does not imply one model for both
  tasks

### Phase 4: split tooling names

Recommended future change:

* separate block-feature export tool from boundary-feature export tool
* stop using one `layout_model_tool` name for both

### Phase 5: distillation v1 only after cleanup

Only after the above cleanup should the project advance to:

* `Task A` rule-gated hint design
* `PubTables` specialist experiment
* future external PDF quality gating

## Next Execution Plan

1. keep current `HGB` distillation v0 scoped to `Task A`
2. explicitly exclude boundary/layout labels from the text-block distillation
   path
3. audit and prune legacy path fallbacks and mixed debug manifests
4. keep `PubTables` specialist under `Task A` only for `table_like` and weak
   `caption`
5. if a future runtime proposal is ever made, separate `Task A` and `Task B`
   providers before discussing any hook
