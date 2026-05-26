# Dataset Registry Notes

Shared dataset audit tables live here:

* `dataset_audit.tsv`
* `source_catalog.tsv`

They remain separate because they answer different questions:

* `dataset_audit.tsv` tracks dataset-level license, redistribution, and task
  fit.
* `source_catalog.tsv` tracks item-level or source-family provenance for small
  tracked documents and audit candidates.

If a future unified registry is needed, it should be generated from these two
sources rather than replacing them ad hoc.
