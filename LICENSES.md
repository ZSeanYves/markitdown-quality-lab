# License and Provenance Summary

This document summarizes source provenance and redistribution status for
`markitdown-quality-lab`. It is a repository maintenance note, not legal
advice.

The governing rule is simple: only keep samples whose source, license, and
intended use are traceable. If provenance, privacy, or redistribution
boundaries are unclear, the sample must stay out of the formal manifest or be
recorded as a blocker until the evidence is closed.

Sample licenses apply to the samples themselves. They do not relicense the
`markitdown` codebase.

## Current formal status

- `external_quality/SOURCE_CATALOG.tsv` currently contains 50 sources, and all
  50 are marked `redistributable=ok`.
- `external_quality/MANIFEST.tsv` currently contains 340 formal rows, and all
  340 are marked `license_review_status=approved`.
- `external_bench/MANIFEST.tsv` currently contains 131 `accepted` rows and
  9 `missing_candidate` placeholders.
- `external_main_process/` is the repo-owned main-process regression surface.
  It is not treated as a third-party source catalog and is summarized here only
  when specific repo-owned files are promoted into `external_quality/`.

## Evidence registries

- `external_quality/SOURCE_CATALOG.tsv` is the machine-readable source,
  license, and provenance index for the formal quality corpus.
- `external_quality/MANIFEST.tsv` is the machine-readable entrypoint for formal
  quality rows.
- `external_bench/MANIFEST.tsv` is the machine-readable entrypoint for the
  curated benchmark corpus.
- `external_main_process/README.md` documents the repo-owned main-process
  regression surface and its boundaries.
- `external_bench/_audit/PROVENANCE.md` records the local provenance review for
  the accepted `copied_from_external_bench` rows.
- `external_quality/audio/vosk-api/_audit/PROVENANCE.md`,
  `external_quality/ocr/_audit/PROVENANCE.md`,
  `external_quality/pdf/irs/_audit/PROVENANCE.md`,
  `external_quality/pdf/niosh/_audit/PROVENANCE.md`, and
  `external_quality/pdf/nist/_audit/PROVENANCE.md` record the local public
  provenance closure notes used by retained OCR and PDF source groups.

## `external_quality` license snapshot

The table below is derived from `external_quality/SOURCE_CATALOG.tsv`.

| License / SPDX | Source count | Representative sources | Notes |
| --- | ---: | --- | --- |
| Apache-2.0 | 11 | `pdfbox_tests`, `pdfjs_tests`, `apache_poi_tests`, `markitdown_repo_samples`, `markitdown_repo_json_samples`, `odf_toolkit_tests`, `vosk_api_examples` | Local license mirrors or notice files are retained for major third-party fixture groups. Repo-owned samples are covered by the main repository Apache-2.0 license mirror. |
| BSD-2-Clause | 2 | `xlsxwriter_examples`, `commonmark_tools_templates` | Keep upstream BSD notice obligations with the mirrored fixture material. |
| BSD-3-Clause | 8 | `python_markdown_docs`, `python_markdown_tests`, `pandas_repo_docs`, `jsonlines_tests`, `jupyterlab_notebooks` | Python-Markdown and Jupyter-related external docs and fixtures remain tracked with their upstream BSD-family terms. |
| CC-BY-2.0 | 1 | `ocr_src_0025` | Commons/Flickr OCR material requires attribution in downstream publication contexts. |
| CC-BY-4.0 | 2 | `idpf_epub_testsuite`, `idpf_epub_testsuite_pls` | Attribution is still required for public redistribution. |
| CC-BY-SA | 1 | `mdn_content_pages` | Documentation samples must preserve attribution and share-alike boundaries. |
| CC0 | 1 | `ocr_src_0031` | Commons CC0 OCR material still requires source-origin retention in repository metadata. |
| CC0-1.0 | 1 | `jsonl_datasets` | Public-domain style open data; keep the upstream license text and source origin. |
| LPPL-1.3c | 1 | `latex2e_samples` | Retain upstream LPPL context with the mirrored LaTeX sample set. |
| MIT | 8 | `toml_test_suite`, `python_docx_tests`, `python_pptx_tests`, `openxml_sdk_tests`, `yaml_test_suite`, `asciidoctor_docs` | Local MIT license mirrors are retained for the promoted third-party fixture groups that need them. |
| NIST Technical Series public-domain in U.S. with worldwide reprint grant | 1 | `pdf_src_0004` | Retain the exact publication URL and the NIST source-group audit note. |
| PDM-1.0 | 1 | `ocr_src_0023` | Commons public-domain-mark OCR material remains anchored by the exact Commons file page. |
| PSF-2.0 | 1 | `cpython_xml_tests` | The mirrored CPython XML fixture group keeps a local PSF license copy. |
| Public domain | 4 | `ocr_src_0028`, `ocr_src_0029`, `ocr_src_0030`, `ocr_src_0032` | Commons historical OCR sources remain documented in the local OCR provenance note. |
| Public-Domain | 1 | `docutils_rst_docs` | Keep source origin and any mirrored upstream licensing context with the tracked docutils material. |
| U.S. government works on IRS.gov with per-file review | 1 | `pdf_src_0001` | Formal retention relies on exact IRS URLs and the local per-file audit note. |
| U.S. government works with per-file review | 1 | `ocr_src_0020` | Formal retention relies on the OCR IRS source-group review note and exact upstream origin. |
| USGov-PD-reviewed | 1 | `irs_forms_public` | The retained IRS form group is supported by exact URLs and local per-file review records. |
| project-owned synthetic | 1 | `ocr_src_0027` | Project-owned synthetic OCR samples are documented as locally generated fixtures. |
| public-domain dedication | 1 | `ocr_src_0022` | Commons own-work OCR sample retained under a public-domain dedication. |
| public_domain | 1 | `niosh_publications` | Retention relies on the local NIOSH per-file public-domain note and exact publication URLs. |

Repo-owned note:

- `markitdown_repo_samples`, `markitdown_repo_pdf_samples`,
  `markitdown_repo_office_samples`, and `markitdown_repo_json_samples` are the
  explicit repo-owned source entries that bridge project-controlled material
  from `external_quality/repo_local/` or `external_main_process/` into the
  formal `external_quality` provenance model.

## `external_bench` provenance posture

`external_bench/` does not currently maintain a separate source catalog in the
same schema as `external_quality/`. The formal benchmark surface is instead
described by:

- row-level source anchors in `external_bench/MANIFEST.tsv`
- local provenance review notes in `external_bench/_audit/PROVENANCE.md`
- repository-level README guidance for benchmark-surface boundaries

This release round closed the local provenance note for the 24 accepted
`copied_from_external_bench` rows. The reviewed public source families include:

- RFC and IETF text documents
- USGS earthquake CSV feed snapshots
- Our World in Data CC BY dataset snapshots
- UniProt TSV REST exports
- SPDX JSON data
- World Bank API snapshots
- W3C HTML specifications
- Project Gutenberg EPUB and ZIP content
- U.S. government and NIST PDF publications
- UK OGL workbook and DOCX sources

The remaining accepted `external_bench` rows are either repo-local samples,
generated tracked payloads, or payloads copied from already-reviewed
`external_quality` source groups.

Current benchmark conclusion:

- No obvious formal infringement blocker is currently known inside the accepted
  `external_bench` manifest rows.
- The main residual caution is temporal rather than legal: some public feed or
  API-backed rows are checked-in snapshots of dynamic upstream endpoints.

## Compliance rules

- Do not allow `UNKNOWN`, empty license fields, or `needs_review` licenses into
  the formal license-complete catalog state.
- Do not allow formal manifest rows without a traceable source origin.
- Do not allow private, local-only, cache, staging, or temporary-download
  files into the formal publish surface.
- Do not misstate sample licenses as project-code licenses.
- Preserve upstream license, notice, attribution, and redistribution
  obligations for third-party fixture groups.
- Preserve exact source URLs and review notes even for government or
  public-domain style material.
- If provenance, license, privacy, or redistribution boundaries are unclear,
  disable the row, remove it from the formal manifest, or record it as a
  blocker.

## Recent removals and resolved blockers

- `microsoft_markitdown_tests`, `pandoc_tests`,
  `paddleocr_ppstructure_samples`, `cdla`, and `markitdown_tests` were removed
  from the formal `external_quality` catalog and manifest because no
  publish-ready local license evidence was retained.
- `tablebank` and `publaynet` were removed from the formal
  `external_quality` source catalog because they remained review-only notes
  without publish-ready redistribution evidence in this repository.
- The `csv-spectrum` CSV fixtures and JSON companion fixtures were removed from
  the formal `external_quality` catalog and manifest after review of both the
  upstream git repository and the npm package evidence. The repository now uses
  repo-owned JSON fixtures instead of those weaker third-party companion files.

## Update procedure

1. After changing samples, manifests, or source catalogs, rerun the relevant
   source and license checks.
2. Update this summary so it stays consistent with the machine-readable files.
3. Do not hand-write claims here that contradict `SOURCE_CATALOG.tsv` or
   `MANIFEST.tsv`.
4. When a blocker is resolved, update the manifest or catalog status together
   with this summary and any supporting audit note.
