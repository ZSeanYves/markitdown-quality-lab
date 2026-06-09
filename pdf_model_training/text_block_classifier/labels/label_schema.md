# Text Block Classifier Label Schema

Layer:

* `convert/pdf`

Purpose:

* assist convert-layer mapping from parser-produced PDF text flow into block
  semantics

The model emits soft hints, confidence, and abstain/low-confidence flags. It
does not rewrite parser-owned canonical layout.

## Primary Labels

| label | use | current source support | runtime eligibility |
| --- | --- | --- | --- |
| `heading` | title-like or section-heading block | strong DocLayNet support from `Title` and `Section-header` | candidate hint only |
| `paragraph` | running body text | strong DocLayNet support from `Text` | teacher/report first |
| `caption` | figure/table caption text | strong DocLayNet label, weak association semantics | candidate hint after review |
| `table_like` | table region or table-like text block | strong DocLayNet table region support | candidate hint after review |
| `list_item` | list item text | strong DocLayNet support from `List-item` | candidate hint only |
| `footer_header_noise` | repeated page header/footer noise | strong DocLayNet support from `Page-header` and `Page-footer` | strongest current runtime-distillation candidate |
| `form_row` | key-value or form-row text | weak side-source support only | report-only |
| `link_text` | link or URL-only text | no direct DocLayNet support | report-only |
| `keep_as_text` | usable text outside primary Markdown semantics | medium support from `Footnote` and weak sources | candidate only after manual review |
| `code_like` | code or monospace-like block | no direct DocLayNet support | report-only |
| `footnote_like` | footnote/endnote body or marker-adjacent text | weak DocLayNet support from `Footnote` | report-only until adapter reviewed |
| `page_number_noise` | page number or folio noise | weak/derived from edge-region evidence | report-only until repeated-page validation |
| `separator` | visual separator or decoration line | no direct DocLayNet support | report-only |
| `uncertain` | explicit abstain class for unstable mappings | mapping fallback | never direct runtime action |

## Legacy Compatibility

| legacy label | current label |
| --- | --- |
| `BodyText` | `paragraph` |
| `Heading` | `heading` |
| `Noise` | `footer_header_noise` |
| `HeaderFooter` | `footer_header_noise` |
| `PageNumber` | `page_number_noise` or `footer_header_noise` after review |
| `Caption` | `caption` |
| `TableLike` | `table_like` |
| `Unknown` | `uncertain` |

## Notes

* this schema excludes parser/layout boundary labels
* `uncertain` should remain explicit when mapping is unstable
* `unknown` is legacy-only; new rows should use `uncertain`
* repo-manual legacy labels under `archive/repo_manual_labels/` are historical
  reference only
* runtime proposals must distinguish high-confidence distilled hints from
  teacher/report-only labels
