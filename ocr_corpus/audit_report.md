# OCR Real-World Audit Report

## Current Scope

* real-world OCR corpus audit for the shipped main-CLI image OCR path
* focus on online source discovery, license review, redistribution policy,
  scenario coverage, and manifest discipline
* no runtime or converter changes
* no OCR assertion changes
* no PDF OCR integration work in this round
* no packaging, announcement, or declaration-material work in this directory

## Accepted Source Classes

* self-generated image samples and synthetic generation strategies with clear
  licensing
* public-domain or clearly permissive government/document sources
* public web or dataset references recorded as metadata when redistribution is
  mixed or too large
* local-only captures for receipts, menus, forms, and degraded phone photos

## Rejected Source Classes

* bulk dataset mirrors or large downloads without immediate row-level need
* sources with non-commercial terms when we need commit-safe reusable bytes
* datasets whose maintainers explicitly forbid redistribution of the data
* unclear-license receipt/invoice sources carrying obvious `pii_risk`
* anything that would turn OCR audit into a public-only quality gate

## Coverage Matrix

| Scenario | Current audited source coverage |
| --- | --- |
| `plain_print` | `ocr_src_0001`, `ocr_src_0011`, `ocr_src_0018`, `ocr_src_0020`, `ocr_src_0023` |
| `layout` | `ocr_src_0010`, `ocr_src_0011`, `ocr_src_0012`, `ocr_src_0013`, `ocr_src_0014` |
| `structured` | `ocr_src_0003`, `ocr_src_0006`, `ocr_src_0007`, `ocr_src_0008`, `ocr_src_0020` |
| `degradation` | `ocr_src_0003`, `ocr_src_0005`, `ocr_src_0017`, `ocr_src_0025` |
| `language` | `ocr_src_0003`, `ocr_src_0007`, `ocr_src_0016` |
| `negative` | `ocr_src_0021`, `ocr_src_0022` |
| `scene_text` | `ocr_src_0001`, `ocr_src_0021`, `ocr_src_0022`, `ocr_src_0025` |
| `handwriting` | `ocr_src_0004`, `ocr_src_0005`, `ocr_src_0016` |
| `historical` | `ocr_src_0005`, `ocr_src_0017`, `ocr_src_0018`, `ocr_src_0019`, `ocr_src_0023`, `ocr_src_0026` |
| `synthetic` | `ocr_src_0001` |
| `pdf_page_image` | `ocr_src_0010`, `ocr_src_0011`, `ocr_src_0013`, `ocr_src_0014`, `ocr_src_0018`, `ocr_src_0020`, `ocr_src_0026` |

## P0 Sample Targets

1. clean printed document page
2. multi-column page
3. heading plus paragraph page
4. receipt or invoice
5. form or key-value page
6. table image
7. low-resolution or blurred scan
8. skewed or perspective phone photo
9. multilingual CJK plus Latin
10. Arabic or other non-Latin OCR page
11. historical scan or typewriter page
12. negative image with no useful text
13. chart, signage, or logo with incidental text
14. dense small-font document
15. PDF page rendered to image candidate

## Candidate Rows Pending Download

| Candidate row | Source | Planned scenario | Planned risk tags | Source policy | Why it matters |
| --- | --- | --- | --- | --- | --- |
| `cand_irs_blank_form_page` | `ocr_src_0020` | `plain_print;structured;pdf_page_image` | `clean_print;form_like;key_value_like;digits_amounts_units` | `ok` | Strong blank-form baseline for OCR image input without PII. |
| `cand_doclaynet_multicolumn_page` | `ocr_src_0011` | `layout;pdf_page_image` | `multi_column;mixed_reading_order;dense_text;small_font` | `metadata_only` | Covers reading-order failure risk. |
| `cand_doclaynet_heading_paragraph_page` | `ocr_src_0011` | `layout;plain_print;pdf_page_image` | `heading_paragraph;header_footer;dense_text` | `metadata_only` | Tests section-title separation and page noise. |
| `cand_cord_receipt_local_audit` | `ocr_src_0008` | `structured` | `receipt_like;digits_amounts_units;pii_risk` | `local_only` | Best audited receipt source, but should stay local due sensitivity. |
| `cand_arabic_invoice_metadata` | `ocr_src_0003` | `language;structured;degradation` | `invoice_like;arabic;background_texture` | `metadata_only` | Good Arabic real-world document mix once manually screened. |
| `cand_nist_sd19_handprint_form` | `ocr_src_0004` | `handwriting;structured` | `handwritten;form_like;digits_amounts_units` | `metadata_only` | Covers handwriting and mixed field content. |
| `cand_pubtabnet_table_image` | `ocr_src_0014` | `structured;pdf_page_image` | `table_like;dense_text;small_font` | `metadata_only` | Useful table-only candidate without claiming full Markdown reconstruction. |
| `cand_nod_oldbook_degradation` | `ocr_src_0017` | `degradation;historical` | `blur;low_resolution;historical_scan` | `unknown` | Attractive degradation benchmark if license clears. |
| `cand_xfund_multilingual_form` | `ocr_src_0007` | `language;structured` | `cjk;latin;multilingual;key_value_like` | `forbidden` | Strong multilingual benchmark reference, but not commit-safe. |
| `cand_chronicling_america_dense_page` | `ocr_src_0018` | `historical;plain_print;pdf_page_image` | `dense_text;small_font;multi_column;historical_scan` | `metadata_only` | High-value historical OCR stress from LOC. |
| `cand_commons_pd_sign_negative` | `ocr_src_0022` | `scene_text;negative` | `signage_like;no_text;text_too_sparse` | `ok` | Negative control for incidental text. |
| `cand_commons_ledger_historical` | `ocr_src_0023` | `historical;plain_print` | `historical_scan;typewriter;dense_text;small_font` | `ok` | Public-domain historical ledger candidate. |
| `cand_commons_menu_scene_text` | `ocr_src_0025` | `scene_text;structured;degradation` | `menu_like;perspective;shadow;digits_amounts_units` | `ok` | Phone-photo menu candidate for structured scene text. |
| `cand_irs_pdf_render_small_font` | `ocr_src_0020` | `pdf_page_image;plain_print` | `small_font;dense_text;form_like` | `ok` | Good rendered-page candidate while keeping PDF OCR out of scope. |
| `cand_commons_permission_scan` | `ocr_src_0024` | `plain_print;structured;pdf_page_image` | `clean_print;form_like;metadata_only_candidate` | `metadata_only` | Small freedom-cleared scanned-page fallback if we need one. |

## Rejected Or Pending Sources

| Source or direction | Status | Reason |
| --- | --- | --- |
| `FUNSD` | rejected for payload bytes | Official terms are non-commercial and depend on RVL-CDIP image rights. |
| `XFUND` | rejected for payload bytes | CC BY-NC-SA 4.0 blocks open downstream redistribution. |
| `DocBank` | rejected for payload bytes | Repo code is Apache-2.0, but README explicitly says not to re-distribute the data. |
| `HICMA` | rejected for payload bytes | CC BY-NC 4.0 blocks commit-safe reuse. |
| `SROIE 2019` | pending | Official redistribution terms were not captured clearly in this audit and receipts carry `pii_risk`. |
| `TableBank` | pending | Public page was reachable, but explicit redistribution terms were not confirmed in this audit. |
| `PubTables-1M` | pending | Official repo was reachable, but the exact dataset license page on the data host was not captured. |
| `NOD` | pending | Useful degradation benchmark, but the current audited Zenodo snapshot did not expose a clear license line. |
| `RVL-CDIP / Tobacco3482 / IIT-CDIP` | pending or rejected | Large legacy scanned-document sources remain high-value references, but rights and redistribution constraints need a separate deep dive. |
| `Kaggle OCR datasets` | pending | Per-dataset licenses vary widely and often require account-level inspection. |
| `Roboflow OCR datasets` | pending | Terms vary per project and often need item-level downstream review. |

## Open Questions

* whether `manifest.tsv` should continue to carry metadata-only planning rows or
  whether all planning should eventually move into `audit_report.md`
* whether we want a dedicated `source_review_status` column later, or whether
  `redistribution` plus `notes` is enough
* which `ok` sources should be used first for tiny checked-in samples without
  diluting the current `ocr_samples` synthetic baseline
* whether we want a future helper that validates `source_catalog.tsv` note style
  and policy tags without touching payload bytes

## Next Action Checklist

* pick 2 to 4 `ok` or `metadata_only` sources and extract only tiny candidate
  page images
* stage any sensitive receipt/invoice/menu examples under `local_only/` only
* review one `historical`, one `language`, and one `scene_text` source at
  item-level granularity
* keep semantic hint wording observational only and avoid over-claim language
