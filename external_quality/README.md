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
* `markdown/`
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

Current expansion snapshot:

* Markdown now includes a small BSD-3-Clause Python-Markdown fixture subset
  under `markdown/python-markdown/`, focused on native footnote references,
  missing-body fallback, wrapped definitions, and larger footnote sets.
* PDF rows now reuse audited official IRS and NIOSH payloads from the existing
  `pdf/irs/` and `pdf/niosh/` source trees for form/table, image-heavy, and
  public-domain manual coverage.
* Existing Apache POI and Open XML SDK DOCX rows are aligned with current
  document-level note definitions: footnotes/endnotes are expected as Markdown
  definitions, while comments remain a normal body appendix.
* Real external EPUB and HTML coverage is still strongest for spine/nav/links
  and safe structural extraction. Explicit strong noteref coverage remains
  primarily covered by repo-local synthetic samples until a small
  license-clear external noteref EPUB/HTML source is selected.
