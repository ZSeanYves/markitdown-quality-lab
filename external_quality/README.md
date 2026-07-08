# External Quality

This tree holds external real-world quality corpus material for `markitdown`.
It is the formal external quality-regression surface, but it remains optional
and repo-local rather than a required runtime dependency.

Structure rules:

- organize first by format, then by source
- keep tracked payloads under `external_quality/<format>/<source>/...`
- keep migration-era manifest rows under `_quality_rows_staging/`
- keep legacy or uncertain material under `archive/`
- keep legacy one-off tooling under `_tools/`

Important boundaries:

- this tree is optional and repo-local
- it is not a runtime dependency of the main repository
- it is not a public-only gate
- large local-only data, provider outputs, and `.tmp` artifacts do not belong
  here as tracked files

Formal control points:

- `MANIFEST.tsv` is the formal row-level consumption contract
- `SOURCE_CATALOG.tsv` is the formal source, license, and provenance index
- README summaries must stay consistent with those two machine-readable files

Current format roots include:

- `audio/`
- `csv/`
- `docx/`
- `epub/`
- `html/`
- `ipynb/`
- `json/`
- `jsonl/`
- `markdown/`
- `ndjson/`
- `ocr/`
- `pdf/`
- `pptx/`
- `toml/`
- `txt/`
- `tsv/`
- `xlsx/`
- `xml/`
- `yaml/`
- `zip/`

Migration note:

- `_quality_rows_staging/` is a migration staging area, not the final ideal
  layout
- legacy path examples may remain under `archive/` for mapping or audit history

Current expansion snapshot:

- Audio now includes an Apache-2.0 `vosk-api` speech example group under
  `audio/vosk-api/`, with the official upstream WAV plus locally derived
  `mp3` and `m4a` transcodes used to cover the current media-pipeline speech
  routes across uncompressed and compressed input variants.
- Markdown now includes a broader BSD-3-Clause Python-Markdown fixture subset
  under `markdown/python-markdown/`, covering footnotes, tables,
  admonitions, and markdown-in-HTML boundary behavior alongside fenced
  example preservation.
- HTML now includes additional CC-BY-SA MDN element pages for `details` and
  `figure`, extending real-page regression coverage for `details/summary`,
  `figure/figcaption`, code examples, and small spec tables.
- YAML now includes extra MIT YAML Test Suite payloads for anchored complex
  keys and tag/directive document streams, preserving the current raw fenced
  fallback behavior as an explicit external contract.
- JSONL now includes a small CC0-1.0 tinytoolkit `jsonl-datasets` subset
  under `jsonl/jsonl-datasets/`, spanning both flat event streams and
  single-column nested chat-format records.
- JSON now relies on repo-owned fixtures under
  `external_main_process/json/markdown` for the small formal JSON coverage that
  previously depended on weaker third-party companion samples.
- PDF rows now reuse audited official IRS and NIOSH payloads from the existing
  `pdf/irs/` and `pdf/niosh/` source trees for form/table, image-heavy, and
  public-domain manual coverage.
- Existing Apache POI and Open XML SDK DOCX rows are aligned with current
  document-level note definitions: footnotes/endnotes are expected as Markdown
  definitions, while comments remain a normal body appendix.
- `ipynb/` now includes a compact BSD-3-Clause Jupyter fixture set spanning
  official `nbformat`, `notebook`, and `jupyterlab` repositories, focused on
  notebook-only semantics such as typed outputs, markdown attachments, raw
  cells, relative links, and image asset materialization.
- Real external EPUB and HTML coverage is still strongest for spine/nav/links
  and safe structural extraction. Explicit strong noteref coverage remains
  primarily covered by repo-local synthetic samples until a small
  license-clear external noteref EPUB/HTML source is selected.
