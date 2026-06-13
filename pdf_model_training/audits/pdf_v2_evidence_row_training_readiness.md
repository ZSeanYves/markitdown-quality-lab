# PDF v2 EvidenceRow Training Readiness

Date: 2026-06-13

Main repo baseline:

* `56730ad pdf_v2: prepare non-semantic parity and signals for model training`

Quality-lab baseline:

* `b30f0fc text-block: audit classifier feature gaps`

## Scope

This step prepares quality-lab ingestion for main-repo PDF v2 exported
`EvidenceRow` signals.

This step does:

* summarize the main-repo flat export contract
* add a shared adapter for TSV/JSONL `EvidenceRow` ingestion
* enforce label and split discipline in tiny fixture tests
* document routing for the two future helper families

This step does not:

* train any model
* download data
* change main-repo product conversion behavior
* change sample expected files
* add runtime inference

## Main-repo export contract summary

Current flat export families:

* `TextFlowRow`
* `BoundaryRow`
* `ArtifactRow`
* `AdjacencyRow`
* `EvidenceRow`

Current `EvidenceRow` kinds:

* `cross_page_boundary`
* `image_text_boundary`
* `header_footer_variant`
* `heading_boundary`
* `column_layout`

Stable source fields used by quality-lab:

* `schema_version`
* `row_family`
* `doc_id`
* `row_id`
* `task`
* `split`
* `page_index`
* `evidence_kind`
* `subject_id`
* `related_id`
* `text`
* `normalized_text`
* `current_rule_confidence`
* `weak_label`
* `gold_label`
* `label_source`
* `reason_tags`
* `risk_tags`
* `source_refs`
* `blockers`
* `extra`

Important flattening note:

* main-repo `EvidenceRow.confidence` is flattened into
  `current_rule_confidence`

Determinism and missing values:

* TSV header order is fixed
* JSONL row serialization is deterministic
* list fields use `|` in TSV and `[]` arrays in JSONL
* missing scalar values stay empty

Doc id policy:

* quality-lab preserves caller-provided `doc_id`
* real corpus builds must ensure that `doc_id` is already privacy-safe

## Quality-lab adapter readiness

Added shared adapter:

* `pdf_model_training/shared/scripts/pdf_v2_evidence_row_adapter.py`

The adapter currently:

* reads flat TSV or JSONL exports
* ignores non-`EvidenceRow` families
* validates `task` and `evidence_kind` routing consistency
* preserves `subject_id`, `related_id`, `source_refs`, `reason_tags`,
  `risk_tags`, and `blockers`
* writes a tiny routed adapter TSV with:
  * `target_model`
  * `target_kind`
  * `lane_status`
  * `label_status`
  * `group_id`
* rejects document-group split leakage across non-`unknown` splits

Added tracked synthetic fixtures and tests:

* `pdf_model_training/shared/scripts/testdata/pdf_v2_evidence_row_fixture.tsv`
* `pdf_model_training/shared/scripts/testdata/pdf_v2_evidence_row_fixture.jsonl`
* `pdf_model_training/shared/scripts/test_pdf_v2_evidence_row_adapter.py`

## Two-model plan

### Layout Recovery Helper

Current routed `EvidenceRow` kinds:

* `header_footer_variant`
* `column_layout`

Interpretation:

* parser/layout-facing weak or unlabeled signals
* suitable for local-only scaffold rows
* not a replacement for DocLayNet gold region supervision

DocLayNet relationship:

* DocLayNet remains the preferred gold region source
* `EvidenceRow` layout signals are supplementary project-exported weak inputs
* DocLayNet labels should supervise layout regions, not Markdown semantics

### Semantic Arbitration Helper

Current routed `EvidenceRow` kinds:

* `cross_page_boundary`
* `image_text_boundary`
* `heading_boundary`

Interpretation:

* relation-style convert-side semantic evidence
* not the same as the current checked `text_block_classifier` mainline
* kept as a future lane in shared contracts until a dedicated tree is justified

DocLayNet relationship:

* DocLayNet does not directly supervise these Markdown-semantic relation
  decisions
* any later mapping from DocLayNet must stay explicit and auditable
* DocLayNet labels must not be treated as automatic semantic gold

## Label policy

Enforced in adapter and docs:

* `gold_label` must be reviewed/manual
* `weak_label` must be rule-derived or parser-fact-derived
* unlabeled rows are allowed
* product expected Markdown is not automatic gold
* rows carrying both `gold_label` and `weak_label` are rejected by the shared
  adapter contract

## Split policy

Current adapter behavior:

* preserves source `split`
* sets `group_id=doc_id`
* rejects one `doc_id` appearing under multiple non-`unknown` split values in
  the same adapted export

Operational expectation for real corpus builds:

* keep document-grouped splits
* do not leak page/block rows across train/dev/heldout
* keep real adapted corpora local-only

## Blockers before real training

Current blockers remain:

* no dedicated `semantic_arbitration` training tree exists yet
* no reviewed real gold labels were added in this pass
* main-repo exported `EvidenceRow` corpora still need local-only manifest and
  split assignment when real documents are prepared
* `EvidenceRow` confidence currently arrives through flat
  `current_rule_confidence`, so downstream readers must keep that mapping
  explicit

## Validation

Validation run for this step:

* `python3 pdf_model_training/shared/scripts/test_pdf_v2_evidence_row_adapter.py`

Results:

* TSV fixture parse passed
* JSONL fixture parse passed
* routing checks passed
* gold/weak separation checks passed
* grouped split leakage rejection check passed

## Explicit confirmation

* no model training was performed
* no model runtime inference was added
* no external data download was performed
