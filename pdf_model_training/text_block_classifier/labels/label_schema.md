# Text Block Classifier Label Schema

Layer:

* `convert/pdf`

Purpose:

* assist convert-layer mapping from PDF text flow into block semantics

Primary labels:

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

Legacy compatibility:

* `BodyText` -> `paragraph`
* `Heading` -> `heading`
* `Noise` -> `footer_header_noise`
* `HeaderFooter` -> `footer_header_noise`
* `PageNumber` -> `footer_header_noise`
* `Caption` -> `caption`
* `TableLike` -> `table_like`
* `Unknown` -> `unknown`

Notes:

* this schema excludes parser/layout boundary labels
* `unknown` and `uncertain` should remain explicit when mapping is unstable
* repo-manual legacy labels under `archive/repo_manual_labels/` are historical
  reference only
