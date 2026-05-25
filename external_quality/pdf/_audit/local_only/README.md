# PDF Local-Only Area

This subtree is reserved for PDF payloads and notes that are useful for audit
but must not be committed.

Typical uses:

* PDFs with unclear redistribution terms
* PDFs with unresolved `pii_risk`
* large files kept only for temporary review
* provider outputs or local experiment notes derived from non-committable PDFs

This subtree is git-ignored except for:

* `README.md`
* `manifest.local.example.tsv`

Do not rely on anything under `local_only/` as a shared team artifact.
