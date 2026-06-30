# License and provenance summary

本文是 `markitdown-quality-lab` 样例来源和授权追溯汇总，不是法律意见。

本仓的收录原则是：只收录来源可追溯、license 明确、用途可解释的样例。发现授权不明、
source origin 不明、隐私边界不清或再分发边界不清时，相关样例必须移出正式 manifest，
或在进入正式消费面之前标为 blocker。

样例 license 只适用于样例自身，不会把上游样例的 license 传播为 `markitdown` 项目代码
license。

## 数据集级来源

* `external_quality/SOURCE_CATALOG.tsv` 是外部质量回归语料的来源和 license 主索引。
* 当前 `external_bench/` 是策展 benchmark 消费面；来源和 license 信息由
  `external_bench/MANIFEST.tsv` 中的字段以及外仓文档共同约束。
* `pdf_model_training/` 的授权信息需要在该目录内部独立维护。当前可参考
  `pdf_model_training/layout_recovery_model/README.md` 和
  `pdf_model_training/text_block_classifier/README.md`；本文件不汇总其中的训练数据、
  local-only 数据或模型实验资产。

## License 汇总

| Area | License / SPDX | Source count | Representative sources | Notes |
| --- | --- | ---: | --- | --- |
| external_quality | Apache-2.0 | 6 | `pdfbox_tests`, `pdfjs_tests`, `apache_poi_tests`, `markitdown_repo_samples`, `markitdown_repo_pdf_samples`, `qpdf_tests` | 来自 `SOURCE_CATALOG.tsv`；第三方项目样例需保留上游 notice/attribution 要求。 |
| external_quality | Public domain | 4 | `ocr_src_0028`, `ocr_src_0029`, `ocr_src_0030`, `ocr_src_0032` | 来自 `SOURCE_CATALOG.tsv`；public-domain/source origin 仍必须记录。 |
| external_quality | BSD-2-Clause | 3 | `csv_spectrum_repo`, `xlsxwriter_examples`, `csv_spectrum_tests` | 来自 `SOURCE_CATALOG.tsv`；保留上游 license/notice 要求。 |
| external_quality | MIT | 3 | `python_docx_tests`, `python_pptx_tests`, `openxml_sdk_tests` | 来自 `SOURCE_CATALOG.tsv`；保留上游 license/notice 要求。 |
| external_quality | BSD-3-Clause | 2 | `python_markdown_docs`, `python_markdown_tests` | 来自 `SOURCE_CATALOG.tsv`；保留上游 license/notice 要求。 |
| external_quality | CC-BY-4.0 | 2 | `idpf_epub_testsuite`, `idpf_epub_testsuite_pls` | 来自 `SOURCE_CATALOG.tsv`；注意 attribution。 |
| external_quality | Apache-2.0 reported by source, verify dataset terms before use | 1 | `tablebank` | Review blocker 风险较高；dataset terms 需独立确认。 |
| external_quality | CC-BY-2.0 | 1 | `ocr_src_0025` | 来自 `SOURCE_CATALOG.tsv`；注意 attribution。 |
| external_quality | CC-BY-SA | 1 | `mdn_content_pages` | 来自 `SOURCE_CATALOG.tsv`；documentation sample，注意 attribution/share-alike 边界。 |
| external_quality | CC0 | 1 | `ocr_src_0031` | 来自 `SOURCE_CATALOG.tsv`；source origin 仍需保留。 |
| external_quality | CDLA-Permissive reported by PaddleOCR docs, verify before use | 1 | `publaynet` | Review blocker 风险较高；dataset terms 需独立确认。 |
| external_quality | NIST Technical Series public-domain in U.S. with worldwide reprint grant | 1 | `pdf_src_0004` | Government/public-domain style source；仍需记录 origin。 |
| external_quality | PDM-1.0 | 1 | `ocr_src_0023` | 来自 `SOURCE_CATALOG.tsv`；source origin 仍需保留。 |
| external_quality | project-owned synthetic | 1 | `ocr_src_0027` | Project-owned synthetic sample；仍需记录生成/来源说明。 |
| external_quality | PSF-2.0 | 1 | `cpython_xml_tests` | 来自 `SOURCE_CATALOG.tsv`；保留上游 license/notice 要求。 |
| external_quality | public-domain dedication | 1 | `ocr_src_0022` | 来自 `SOURCE_CATALOG.tsv`；source origin 仍需保留。 |
| external_quality | public_domain | 1 | `niosh_publications` | Government/public-domain style source；仍需记录 origin。 |
| external_quality | U.S. government works on IRS.gov with per-file review | 1 | `pdf_src_0001` | Government/public-domain style source；per-file review 仍需保留。 |
| external_quality | U.S. government works with per-file review | 1 | `ocr_src_0020` | Government/public-domain style source；per-file review 仍需保留。 |
| external_quality | USGov-PD-reviewed | 1 | `irs_forms_public` | Government/public-domain style source；review evidence 仍需保留。 |
| external_bench | CC-BY-4.0 | 30 | `pptx_nhs_diabetes`, `csv_owid_co2`, `csv_owid_life_expectancy`, `csv_owid_population`, `tsv_uniprot_reviewed`, ... | 来自 `SOURCE_CATALOG.tsv`；documentation/data samples may require attribution. |
| external_bench | OGL-UK-3.0 | 29 | `docx_rail_cif_notes`, `docx_ulsterbus_cif_notes`, `docx_metro_cif_notes`, `docx_bus_stop_defs`, `docx_dvla_user_guide`, ... | UK public-sector/open-government data；保留 attribution/source origin。 |
| external_bench | LicenseRef-US-Gov-Public-Domain | 23 | `pdf_irs_p17`, `pdf_irs_f1040`, `pdf_irs_p15`, `pdf_nist_800_53r5`, `pdf_nist_800_61r2`, ... | US government/public-domain style source；仍需记录 exact URL and review state。 |
| external_bench | LicenseRef-Project-Gutenberg | 16 | `epub_gutenberg_moby_dick`, `epub_gutenberg_pride`, `epub_gutenberg_frankenstein`, `epub_gutenberg_dracula`, `epub_gutenberg_sherlock`, ... | Project Gutenberg terms apply；保留 header/license context。 |
| external_bench | LicenseRef-IETF-Trust | 10 | `txt_rfc9110`, `txt_rfc9111`, `txt_rfc9112`, `txt_rfc8446`, `txt_rfc8259`, ... | IETF/RFC samples；保留 IETF Trust license information。 |
| external_bench | LicenseRef-W3C-Document-2023 | 10 | `html_w3c_wcag22`, `html_w3c_svg2`, `html_w3c_css_color4`, `html_w3c_css_grid2`, `html_w3c_webaudio`, ... | W3C documentation samples；保留 W3C Document License attribution/boundary。 |
| external_bench | Apache-2.0 | 8 | `yaml_swagger_petstore`, `yaml_k8s_deployment`, `yaml_k8s_simple_pod`, `yaml_k8s_load_balancer`, `yaml_bitnami_nginx_values`, ... | OSS documentation/config samples；保留上游 license/notice 要求。 |
| external_bench | CC0-1.0 | 3 | `json_spdx_licenses`, `json_spdx_exceptions`, `json_wikidata_q42` | Public-domain style / open data; source origin 仍需保留。 |
| external_bench | MIT | 2 | `yaml_actions_node`, `yaml_actions_python` | OSS samples；保留上游 license/notice 要求。 |
| pdf_model_training | not summarized here | 0 | not summarized here | 训练、审计、local-only 和模型实验资产需要在 `pdf_model_training/` 内部独立维护授权信息。 |

## Source catalog schema

`external_quality/SOURCE_CATALOG.tsv` 当前使用的 source/license 字段包括：

* source/origin: `id`, `source_name`, `source_type`, `url`, `local_cache`,
  `proposed_source_id`, `proposed_url`, `proposed_local_path`
* license: `license_status`, `proposed_license`
* review/context: `redistributable`, `recommended_use`, `download_mode`, `priority`,
  `notes`, `migration_note`

`external_bench/MANIFEST.tsv` 当前保留的来源/授权相关字段包括：

* source/origin: `bench_id`, `source_kind`, `source_ref`
* integrity/context: `bytes`, `sha256`, `enabled_tier`, `bench_layers`,
  `tags`, `review_status`, `notes`

两个 catalog 的 schema 不同，不应强行统一。消费端和审计脚本应按各自 schema 读取。

## 合规规则

* 不允许 `UNKNOWN`、空 license 或 `needs_review` license 进入 license-complete catalog 状态。
* 不允许无 source origin 的样例进入正式 manifest。
* 不允许 private、local-only、cache、temporary download 或 staging 文件进入正式 manifest。
* 不允许将 sample license 误写成项目代码 license。
* 第三方项目样例必须保留其 license、notice、attribution 和 redistribution 要求。
* Public-domain / government source 也必须记录 source origin、exact URL 和 review 状态。
* 若 source license、privacy、provenance 或 redistribution 边界不清，样例必须保持 disabled、
  移出正式 manifest，或记录为 open blocker。

## Open blockers / 待处理授权阻断项

The previously blocked sources microsoft_markitdown_tests, pandoc_tests,
paddleocr_ppstructure_samples, cdla, and markitdown_tests were removed from the
formal external_quality manifest and source catalog because no local license
evidence was available.

No open license/source blockers were found in external_quality or external_bench
at the time of this summary.

## 更新方法

1. 修改样例、manifest 或 source catalog 后，重新运行 license/source 检查。
2. 更新本文件中的 license 汇总表和 open blockers。
3. 不要手写与 `SOURCE_CATALOG.tsv` 矛盾的信息。
4. 若 blocker 被解决，应同时更新 catalog、manifest review 状态和本文摘要。
