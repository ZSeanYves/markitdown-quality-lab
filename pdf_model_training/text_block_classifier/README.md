# Text Block Classifier

Purpose:

* assist convert-layer mapping from PDF text flow to block semantics

Layer:

* `convert/pdf`

Target labels:

* `paragraph`
* `heading`
* `footer_header_noise`
* `caption`
* `table_like`
* `form_row`
* `list_item`
* `separator`
* `link_text`
* `keep_as_text`
* `unknown`
* `uncertain`

Dataset sources:

* `DocLayNet` gold source
* `PubLayNet` weak-layout supplement
* `PubTables-1M` table specialist

Current status:

* this directory now owns a full per-model training layout:
  `dataset/`, `adapters/`, `labels/`, `manifests/`, `training/`,
  `evaluation/`, `models/`, `reports/`, `scripts/`, `local_only/`, `archive/`
* PR 1 boundary cleanup keeps legacy mixed assets only as compatibility
  reference:
  * old `pdf_layout_classifier` names remain historical
  * old mixed manifests remain archived
  * old JSON model metadata remain reference-only under `models/`
* `manifests/manifest.tsv` is the only current recommended manifest entrypoint
* the current active manifest is intentionally header-only until mature public
  annotated dataset adapter outputs are reviewed
* repo-manual sanity rows and old manifest drafts have been moved into
  `archive/old_manifests/`
* repo-manual labels are archived under `archive/repo_manual_labels/`
* historical model JSON files remain under `models/` for reference only
* local-only DocLayNet acquisition now has three intended modes:
  `local zip cache` for stable pilot/teacher runs, explicit `download-cache`
  for resumable full-zip caching under `local_only/`, and `remote range smoke`
  only for small recovery checks
* current offline teacher baseline is `HistGradientBoostingClassifier` on
  `baseline_v3` features; current `pilot3000_v1` heldout macro F1 is `0.8097`
* `PubTables-1M` is currently scoped as a specialist source for
  `table_like` and weak `caption` probing only
* current text-block mainline is:
  * DocLayNet adapter outputs
  * baseline feature export
  * HGB teacher training
  * distillation v0 / v1 planning

Next action:

* adapt mature public datasets into block-label exports under local-only flows
* audit and distill the current HGB teacher before any runtime proposal
* keep `PubTables` specialist work isolated from `DocLayNet` gold heldout
* keep gold and weak-source evaluation separate
* do not reactivate repo-manual sample manifests as the recommended training
  route
* prefer `--core-zip` / `--extra-zip` or `--download-cache` for `pilot500_v1`
  and larger DocLayNet subsets; do not rely on remote range for large runs

Do not mix:

* parser/layout boundary rows from `layout_recovery_model`
* `PubLayNet` weak rows into `DocLayNet` gold eval
* repo-manual sanity labels into the current recommended manifest
* legacy `pdf_layout_classifier` compatibility assets into the current mainline
