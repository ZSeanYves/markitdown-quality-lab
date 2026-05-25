# External Quality

This tree holds external real-world quality corpus material for `markitdown`.

Structure rules:

* organize first by format, then by source
* keep tracked payloads under `external_quality/<format>/<source>/...`
* keep migration-era manifest rows under `_quality_rows_staging/`
* keep legacy or uncertain material under `archive/`
* keep legacy one-off tooling under `_tools/`

Important boundaries:

* this tree is optional and repo-local
* it is not a runtime dependency of the main repository
* it is not a public-only gate
* large local-only data, provider outputs, and `.tmp` artifacts do not belong here as tracked files

Current format roots include:

* `csv/`
* `docx/`
* `epub/`
* `html/`
* `json/`
* `ocr/`
* `pdf/`
* `pptx/`
* `txt/`
* `xlsx/`
* `xml/`
* `yaml/`
* `zip/`

Migration note:

* `_quality_rows_staging/` is a migration staging area, not the final ideal layout
* legacy path examples may remain under `archive/` for mapping/audit history
