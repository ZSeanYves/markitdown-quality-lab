# PDF v2 EvidenceRow Contract

This document describes the quality-lab-side ingestion contract for main-repo
PDF v2 `EvidenceRow` exports introduced in main repo commit:

* `56730ad pdf_v2: prepare non-semantic parity and signals for model training`

It is a readiness contract only. It does not start training, define runtime
behavior, or upgrade weak labels into gold.

## Accepted source files

The adapter accepts flat exports produced by main-repo helpers:

* `pdf_v2_dataset_export_to_tsv(...)`
* `pdf_v2_dataset_export_to_jsonl(...)`

The flat export may contain multiple row families. The quality-lab adapter
filters for:

* `row_family=EvidenceRow`

Other row families are ignored by the shared readiness adapter.

## Stable source row families

Current flat export families are:

* `TextFlowRow`
* `BoundaryRow`
* `ArtifactRow`
* `AdjacencyRow`
* `EvidenceRow`

Current `EvidenceRow` kinds are:

* `cross_page_boundary`
* `image_text_boundary`
* `header_footer_variant`
* `heading_boundary`
* `column_layout`

Routing expectations are versioned in:

* `pdf_v2_evidence_row_routing.tsv`

## Stable keys and fields

The flat export keeps deterministic row ids via:

* `row_id`
* `doc_id`
* `page_index`
* `subject_id`
* `related_id`

For `EvidenceRow`, the fields that quality-lab currently treats as stable are:

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
* `risk_tags`
* `reason_tags`
* `source_refs`
* `blockers`
* `extra`

Important flattening note:

* `EvidenceRow.confidence` is flattened into
  `current_rule_confidence` in TSV/JSONL.
* `current_rule_decision` stays empty for `EvidenceRow`.

## Label policy

Quality-lab ingestion enforces:

* `gold_label` means reviewed/manual only.
* `weak_label` means rule-derived or parser-fact-derived only.
* unlabeled rows are valid.
* a row must not carry both `gold_label` and `weak_label` under the current
  shared adapter contract.
* product expected Markdown is not automatic gold.

Recommended `label_source` interpretation:

* `manual_review`, `human_review`, or another explicit reviewed/manual source:
  eligible for `gold_label`
* `rule_decision`, `parser_fact`, or another explicit weak/rule source:
  eligible for `weak_label`
* `none`: unlabeled

## Privacy-safe doc id policy

Main-repo export keeps caller-provided `doc_id`.

Quality-lab does not hash or rewrite it in the shared readiness adapter.
Therefore:

* `doc_id` should already be privacy-safe before export
* `group_id` for split grouping is currently equal to `doc_id`
* path-like or unsafe ids must be reviewed before any real corpus build

## Determinism and missing-field representation

Main-repo export guarantees:

* deterministic `row_id`
* deterministic TSV header order
* deterministic JSONL line content for the same input rows

Missing-field representation:

* TSV scalar missing value: empty cell
* TSV list missing value: empty cell
* TSV list encoding: `|`-joined values in source order
* JSONL scalar missing value: empty string for flattened rows
* JSONL list missing value: `[]`
* `page_index` is carried as a string in flat exports

## Split discipline

The shared adapter preserves per-row `split` and adds:

* `group_id=doc_id`

It also rejects document-group split leakage:

* one `group_id` must not map to multiple non-`unknown` split values inside the
  same adapted export

## Non-goals

This contract does not:

* define real training manifests
* create gold labels automatically
* turn weak labels into gold
* route rows into product runtime
* claim that `semantic_arbitration` already has a standalone training tree
