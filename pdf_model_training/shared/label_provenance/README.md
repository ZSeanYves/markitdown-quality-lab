# Label Provenance

Track where labels come from and how they were adapted.

Every non-synthetic row should preserve:

* source dataset
* upstream source label
* target model
* target label
* mapping confidence
* adapter version or mapping file
* split
* local-only path if the row is not tracked

Weak-source rows must remain distinguishable from gold rows.

For PDF v2 `EvidenceRow` ingestion:

* `gold_label` must remain reviewed/manual only.
* `weak_label` must remain rule-derived or parser-fact-derived only.
* product expected Markdown must not be treated as automatic gold.
* unlabeled rows are allowed and should stay explicit.
