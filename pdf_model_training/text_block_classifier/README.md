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
* repo-local labels for sanity and project-specific gaps

Current status:

* this directory now owns the historical Task A planning and block-only helper
  scripts
* the current checked manifest is a draft/example with block and schema-review
  rows only, not a production training manifest
* `manifest.block_draft.tsv` is the cleaner block-only draft for future
  text-block intake review
* `manifest.example.tsv` remains as the migrated legacy draft reference
* historical model JSON files remain here for reference only

Next action:

* keep block-label schema stable
* keep adapter exports local-only for larger public datasets
* keep gold and weak-source evaluation separate

Do not mix:

* parser/layout boundary rows from `layout_recovery_model`
* `PubLayNet` weak rows into `DocLayNet` gold eval
