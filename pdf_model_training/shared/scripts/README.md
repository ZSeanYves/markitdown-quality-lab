# Shared Scripts

Shared scripts are for cross-model adapter and schema checks that should not
live under only one model tree.

Current scope:

* PDF v2 `EvidenceRow` ingestion
* tiny synthetic fixture validation
* routing and label-discipline checks

These scripts do not:

* download datasets
* train models
* generate large tracked outputs
* modify main-repo product behavior

Prefer writing real adapted outputs to local-only or temporary paths.

Current adapter:

* `pdf_v2_evidence_row_adapter.py`
  * consumes main-repo PDF v2 TSV/JSONL flat exports
  * filters `row_family=EvidenceRow`
  * validates routing and label discipline
  * emits a tiny training-readiness TSV with target-lane routing metadata
