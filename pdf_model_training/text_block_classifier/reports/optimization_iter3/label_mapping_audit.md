# Text Block Classifier Label Mapping Audit Iteration 3

## Scope

- dataset: `DocLayNet pilot3000_v1`
- split reviewed: `heldout`
- baseline run: `pilot3000_v1_hgb_baseline_v3`
- model role: convert-layer soft hint with abstain gate

## Caption

DocLayNet `Caption` is currently mapped directly to `caption`.

Heldout evidence:

| source_label | target_label | support | no-abstain F1 | selected threshold | selected precision | selected coverage |
| --- | --- | --- | --- | --- | --- | --- |
| `Caption` | `caption` | 286 | 0.5849 | 0.95 | 0.9053 | 0.3007 |

Audit notes:

- The mapping is semantically right but operationally weak for runtime because DocLayNet does not encode robust figure/table/image association.
- Caption bbox and recovered text can be split or aligned imperfectly against parser text blocks, especially for long scientific captions and product-model captions.
- Existing features include prefix and neighbor-text proxies, but not true distance to image/table/figure regions.
- Caption should remain a low-coverage, high-precision hint until visual proximity or caption association features exist.
- Runtime threshold should stay stricter than the global threshold; current evidence supports `0.95` for caption hints.

## List Item

DocLayNet `List-item` is currently mapped directly to `list_item`.

Heldout evidence:

| confusion | count | selected-gate accepted errors |
| --- | --- | --- |
| `list_item -> paragraph` | 484 | 240 |
| `paragraph -> list_item` | 327 | 131 |
| `list_item -> heading` | 242 | 113 |

Audit notes:

- The direct mapping is useful but probably too coarse for wrapped and continuation rows.
- Parser block grouping may merge list continuation text into paragraph-like blocks, while DocLayNet still marks the region as `List-item`.
- `list_item` needs either continuation risk flags or derived subfeatures for marker kind, sibling indent similarity, and continuation line count.
- The next feature pass should not split the public label yet; it should add `list_continuation_risk` or `wrapped_line_candidate` as features first.

## Heading

DocLayNet `Title` and `Section-header` are currently mapped to `heading`.

Heldout evidence:

| source_label | target_label | support |
| --- | --- | --- |
| `Title` | `heading` | 169 |
| `Section-header` | `heading` | 1546 |

Major confusions:

| confusion | count | selected-gate accepted errors |
| --- | --- | --- |
| `list_item -> heading` | 242 | 113 |
| `paragraph -> heading` | 218 | 93 |
| `caption -> heading` | 67 | 30 |

Audit notes:

- Mapping both `Title` and `Section-header` to `heading` is acceptable for the current coarse label, but it hides different runtime risks.
- Future schema may need `document_title`, `section_heading`, and `heading_candidate` for audit, but runtime should still consume only gated hints.
- False heading positives likely come from short text, section-like prefixes, capitalization, and visual isolation without enough font/body-density guards.
- Heading runtime use needs a shape guard that combines font-size delta, section prefix, terminal punctuation, and neighbor body density.

## Runtime Label Recommendation

| label | recommendation | threshold note | blocker |
| --- | --- | --- | --- |
| `heading` | keep candidate hint | keep strict per-label threshold near `0.85` | needs font/body-density shape guard |
| `paragraph` | keep candidate hint | global/per-label gate only | not a hard override target |
| `caption` | keep low-coverage hint | keep `0.95` until visual proximity exists | missing visual association |
| `table_like` | keep candidate hint | threshold near `0.75` | table geometry export can improve precision |
| `list_item` | keep candidate hint | threshold near `0.60`, but audit continuation errors | missing line-level continuation |
| `footer_header_noise` | keep strongest candidate hint | threshold can remain low with edge/repetition evidence | needs repeated-page validation before hard removal |
| `keep_as_text` | keep cautious candidate | threshold near `0.75` | source support is medium |
| `page_number_noise` | remove from direct runtime action | no predictions in this run | needs dedicated repeated-page/page-number evidence |
| `uncertain` | remove from direct runtime action | no predictions in this run | abstain class only |

## Report-Only Labels

| label | recommendation | blocker |
| --- | --- | --- |
| `form_row` | keep report-only | DocLayNet does not support it directly |
| `link_text` | keep report-only | needs annotation/link extraction evidence |
| `code_like` | keep report-only | needs monospace/code-source data |
| `separator` | keep report-only | needs visual/vector line evidence |
| `footnote_like` | keep report-only | DocLayNet `Footnote` currently maps to `keep_as_text` for review |

## Label Mapping Changes This Iteration

No checked label mapping changes were made in iteration 3.

Rationale:

- The failures are more consistent with missing features and parser alignment risk than with an obviously wrong mapping table.
- Changing labels before adding visual proximity, line continuation, and heading shape guards would make the audit less reproducible.
- The next training pass should keep the coarse labels stable and add risk/shape/proximity features first.
