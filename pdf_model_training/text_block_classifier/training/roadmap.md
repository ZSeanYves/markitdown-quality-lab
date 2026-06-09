# PDF Text Block Roadmap

## Stage 0 Done

Completed already:

* `DocLayNet` smoke and pilot acquisition
* `baseline_v3` feature work
* offline `HGB` teacher training
* teacher quality beyond the original distillation gate
  * `pilot3000_v1 baseline_v3 HGB heldout macro F1 = 0.8097`

Main conclusion from Stage 0:

* continuing to scale `DocLayNet` pages with only the old logistic baseline was
  misleading
* the stronger offline teacher is good enough to justify distillation work

## Stage 1 Current

Current target:

* HGB teacher artifact audit
* HGB feature-importance and error-bucket audit
* `PubTables` specialist scaffold
* distillation policy hardening
* distillation v0 high-confidence hint export

Deliverables:

* local-only teacher audit reports
* tracked `distillation_policy.md`
* tracked `PubTables` specialist adapter skeleton
* tracked roadmap and specialist notes
* tracked hint-export script plus local-only v0 eval

Stage 1 status:

* teacher audit done
* `PubTables` scaffold done
* distillation v0 hint export done
* boundary audit shows the old `pdf_layout_classifier` route mixed block and
  boundary tasks
* PR 1 boundary cleanup now marks legacy model metadata and compatibility
  scripts explicitly as historical surfaces
* v1 gated hint design now exists as a report-only heldout evaluator
* current v1 best dry-run candidate is `footer_header_noise`
* next step is external-quality dry-run planning, not runtime hookup

## Stage 2 Next

Next target:

* return to offline PDF model work after the 2026-05-31 external-quality
  expansion checkpoint
* tiny real `PubTables` local-only adapter smoke
* narrow `table_like` / weak `caption` specialist experiment
* teacher + specialist evaluation on boundary slices
* explicit source-separated evaluation
* v1 rule-gated hint design for stable labels
* external-quality report-only dry-run planning for v1 labels

Rules for Stage 2:

* do not pollute `DocLayNet` gold heldout
* keep `PubTables` as specialist-only
* treat `caption` as weak/specialist until proven stable
* clean up legacy mixed block/boundary references before any v1 hint proposal

## Stage 3 Distillation

Distillation target:

* high-confidence routing thresholds
* rule candidates for stable buckets
* compact decision-table candidates
* possible small model candidates if speed and closure stay controlled

Primary buckets to distill first:

* `footer_header_noise`
* `heading`
* `keep_as_text`
* only later:
  * `table_like`
  * high-confidence `paragraph`
  * high-confidence `list_item`

Buckets that still need caution:

* `caption`
* patent/legal short-numbered lines
* address / affiliation rows
* form-like short rows
* anything inherited from old boundary/layout manifests

Current v1 interpretation:

* `footer_header_noise`, `heading`, and `keep_as_text` are the only v1 gate
  candidates
* `paragraph`, `list_item`, `table_like`, and `caption` stay outside the v1
  gated surface
* after the first heldout pass:
  * `footer_header_noise` is ready for an external-quality dry run
  * `heading` and `keep_as_text` still need more guard refinement

## Stage 3.5 Cooperative Gate

Immediate next target:

* rule-model cooperative scoring
* profile comparison:
  * conservative
  * balanced
  * model-heavy
* identify a dry-run-ready profile without fighting the existing rules

Requirements:

* rules remain primary
* hard conflicts block regardless of model confidence
* emitted hints stay report-only
* runtime proposal remains paused

Current first-pass result:

* raw v1 baseline:
  * emitted rows `1219`
  * coverage `0.1096`
  * emitted accuracy `0.9779`
* best current cooperative profile:
  * `conservative @ 0.85`
  * emitted rows `698`
  * coverage `0.0628`
  * emitted accuracy `0.9957`
  * wrong emitted `3`

Interpretation:

* the cooperative gate is doing the right kind of work:
  * lower coverage
  * lower wrong-emitted risk
  * stronger agreement with rule evidence
* `footer_header_noise` remains the best dry-run candidate
* `heading` and `keep_as_text` still need more guard refinement before they
  should move to an external-quality dry run

## Stage 3.7 Quality Expansion Checkpoint

Checkpoint: 2026-05-31

Status:

* external-quality expansion checkpoint is complete
* `bash samples/check.sh` is green
* `bash samples/check_quality.sh` is green on the expanded ready corpus
* `bash samples/check_quality.sh --format pdf` is green
* per-format quality checks are green
* runtime proposal remains paused

Interpretation:

* the converter-quality baseline is clean enough to return to offline PDF
  model training and evaluation
* remaining quality expansion items are follow-up coverage work, not blockers:
  * HTML strong/conservative noteref external samples remain thin
  * EPUB strong-noteref external samples remain thin
  * PDF footnote body association is still unimplemented
  * metadata sidecar `note_definitions` serialization remains future work
* external-quality should be used as a regression guard, not as unreviewed model
  training gold
* `DocLayNet`, `PubTables`, and model-specific corpora remain the training/eval
  sources

See also:

* `../../audits/pdf_model_return_checkpoint.md`

## Stage 3.9 Overnight Goal And Runtime Blockers

Checkpoint: 2026-05-31

Status:

* the overnight offline PDF model goal is complete
* `pilot3000_v1` / `baseline_v3` HGB remains the best current
  `text_block_classifier` teacher
  * heldout macro F1 `0.8097`
  * heldout accuracy `0.8269`
* offline teacher quality is good enough for continued report-only
  distillation work
* runtime integration remains blocked

Current blockers:

* `footer_header_noise` has the only promising external-quality report-only
  path, but its manual-review TSV still has no filled reviewer decisions
* `heading` and `keep_as_text` are not safe default emit labels
* `layout_recovery` is blocked by Task B data readiness, not model code
* external-quality remains validation/report-only data, not training gold

Next phase:

* finish the `footer_header_noise` manual review and rerun the summary
* acquire mature Task B data for `layout_recovery`
* only after both blockers clear, consider a disabled-by-default runtime
  proposal

See also:

* `../../audits/overnight_pdf_model_goal_report.md`
* `../../audits/footer_header_noise_manual_review_blocker.md`
* `../../audits/layout_recovery_model_data_readiness.md`

## Stage 4 Runtime Preconditions

Only after distillation evidence is mature should runtime be discussed.

Required gates:

* external PDF quality evaluation
* `bash samples/check.sh`
* `bash samples/check_quality.sh --format pdf`
* `bash samples/bench.sh`
* speed regression review
* binary / closure review
* fail-closed behavior review

Only then:

* propose convert-layer gated integration
* keep deterministic rules primary
* keep model influence optional and reversible

## Stage 3.8 External Quality Scaffold

Current tracked scaffold:

* `scripts/run_external_quality_hint_dry_run.py`
* `scripts/export_footer_header_manual_review.py`
* `scripts/summarize_footer_header_manual_review.py`
* `scripts/export_footer_header_review_visual_pack.py`
* `training/footer_header_noise_report_only_package.md`

Current status:

* `footer_header_noise` only
* report-only only
* can reuse the normal external-quality PDF path without mutating outputs
* can export legacy block candidates for side-channel review
* now includes a tracked bridge from external PDF block candidates to
  `baseline_v3` / `HGB` cooperative features
* `smoke20_v2` capability is `ready`
  * rows `20`
  * candidates `135`
  * emitted hints `12`
* `pdf_all_v2` capability is `ready`
  * rows `77`
  * candidates `360`
  * emitted hints `12`
* `pdf_all_v3_footer_refined` capability is `ready`
  * rows `77`
  * candidates `360`
  * emitted hints `6`
* current recommended external-quality profile is `conservative_v2`
  * `model_confidence_threshold = 0.95`
  * `cooperative_threshold = 0.85`
* current non-emit majority is teacher label disagreement
  * `heading`
  * `paragraph`
  * `table_like`
* footer/header refinement now blocks dense multi-column edge-row booking cells
  that slipped through `pdf_all_v2`
* current emitted examples are now only the isolated page-number-style shells
  from the `md_test` / section-numbering variants
* body-risk rows with `central_body_band` / `sentence_like` signals remain
  blocked from emission in this pass
* `footer_header_noise` is the only label ready for the next external-quality
  manual-review stage
* a manual-review export package now exists as the next tracked preparation
  layer before any larger benchmark claim
* a manual-review summary step now exists so reviewer decisions can be turned
  into a keep/refine/adjust/expand recommendation without touching runtime
* a manual-review visual-pack step now exists so reviewers can audit against
  resolved PDF paths, quality outputs, and optional page/crop renders instead
  of a bare TSV

Immediate next step from this scaffold:

* keep `footer_header_noise` on the refined `conservative_v2` path unless
  another false-positive cluster appears
* export the visual pack before asking for reviewer decisions
* use `v1_visual/review_index.md` or `v1_visual/review_index.html` as the
  primary review surface
* open `footer_header_manual_review.tsv` and fill `reviewer_decision` /
  `reviewer_notes`
* run `scripts/summarize_footer_header_manual_review.py`
* use the summary to decide whether to keep the profile, refine guards, adjust
  threshold, or expand the benchmark
* export and review the manual-review package before any broader benchmark claim
* if manual review is clean, prepare a larger external-quality footer/header
  report-only benchmark
* if manual review finds a new failure cluster, refine guards again
* expand external-quality coverage through larger/manual review before any
  runtime discussion
* keep `heading` / `keep_as_text` as later report-only expansions and paused in
  this lane
* if `PyMuPDF/fitz` is missing locally, allow path-only visual-pack fallback
  instead of blocking the report-only review workflow
* continue `PubTables` specialist work separately
* keep runtime proposal paused until after more external-quality evidence
