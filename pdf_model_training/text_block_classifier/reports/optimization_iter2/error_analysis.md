# Text Block Classifier Error Analysis Iteration 2

## Scope

- split: `heldout`
- selected_gate: `confidence_only`
- confidence_threshold: `0.70`
- margin_threshold: `none`
- model role: convert-layer soft hint with abstain gate

## Caption Weakness

- no-abstain caption F1 remains `0.5849` with support `286`.
- DocLayNet `Caption` is useful but does not encode reliable association to the nearest figure/table/image.
- The current baseline has cue features such as caption/table/figure text hints and neighbor cues, but it still lacks geometric association to nearby figures, tables, and images.
- Caption-vs-paragraph errors are concentrated in short text and nearby-context ambiguity, so caption should keep a stricter runtime threshold until association features improve.

## List Item vs Paragraph

- The largest heldout confusion remains `list_item -> paragraph` and `paragraph -> list_item`.
- Existing marker and indent features help, but wrapped-line continuation and hanging-indent context are still not strong enough.
- The next feature pass should add more explicit line-start marker parsing, continuation detection, and parser block alignment diagnostics.

## Paragraph/List Item vs Heading

- `list_item -> heading` and `paragraph -> heading` remain high-volume errors.
- The model likely over-promotes short or visually isolated body/list rows when font/shape signals look title-like.
- Add heading-shape guards using nearby body density, upper/lowercase ratio, section-prefix depth, and gap patterns before retraining.

## Top Confusions

| rank | gold | predicted | count | avg_conf | avg_margin | accepted_errors |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | list_item | paragraph | 484 | 0.7017 | 0.4567 | 240 |
| 2 | paragraph | list_item | 327 | 0.6656 | 0.4141 | 131 |
| 3 | list_item | heading | 242 | 0.6734 | 0.4603 | 113 |
| 4 | paragraph | heading | 218 | 0.6541 | 0.4344 | 93 |
| 5 | paragraph | caption | 110 | 0.6477 | 0.4019 | 46 |
| 6 | heading | list_item | 93 | 0.6044 | 0.3347 | 26 |
| 7 | heading | paragraph | 79 | 0.6563 | 0.4189 | 29 |
| 8 | caption | heading | 67 | 0.7086 | 0.5457 | 30 |
| 9 | paragraph | table_like | 41 | 0.8153 | 0.6711 | 30 |
| 10 | caption | paragraph | 38 | 0.6105 | 0.3538 | 9 |

## Failure Buckets

| rank | gold | predicted | conf_bucket | margin_bucket | count | action |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | list_item | paragraph | 0.70-0.90 | >=0.30 | 158 | feature: strengthen list markers, indentation, and continuation context |
| 2 | list_item | heading | 0.70-0.90 | >=0.30 | 98 | feature/data: add heading-shape guards and clean title-vs-body ambiguity |
| 3 | list_item | paragraph | >=0.90 | >=0.30 | 82 | feature: strengthen list markers, indentation, and continuation context |
| 4 | paragraph | list_item | 0.70-0.90 | >=0.30 | 81 | feature: strengthen list markers, indentation, and continuation context |
| 5 | list_item | paragraph | 0.50-0.70 | 0.15-0.30 | 73 | feature: strengthen list markers, indentation, and continuation context |
| 6 | list_item | paragraph | 0.50-0.70 | >=0.30 | 71 | feature: strengthen list markers, indentation, and continuation context |
| 7 | paragraph | heading | 0.70-0.90 | >=0.30 | 59 | feature/data: add heading-shape guards and clean title-vs-body ambiguity |
| 8 | paragraph | list_item | 0.50-0.70 | >=0.30 | 59 | feature: strengthen list markers, indentation, and continuation context |
| 9 | list_item | heading | 0.50-0.70 | >=0.30 | 52 | feature/data: add heading-shape guards and clean title-vs-body ambiguity |
| 10 | paragraph | list_item | >=0.90 | >=0.30 | 50 | feature: strengthen list markers, indentation, and continuation context |
| 11 | paragraph | list_item | 0.50-0.70 | 0.15-0.30 | 40 | feature: strengthen list markers, indentation, and continuation context |
| 12 | paragraph | heading | 0.50-0.70 | >=0.30 | 35 | feature/data: add heading-shape guards and clean title-vs-body ambiguity |
| 13 | paragraph | caption | 0.70-0.90 | >=0.30 | 35 | feature/data: add caption association and figure/table proximity review |
| 14 | paragraph | heading | >=0.90 | >=0.30 | 34 | feature/data: add heading-shape guards and clean title-vs-body ambiguity |
| 15 | paragraph | heading | <0.50 | 0.05-0.15 | 29 | feature/data: add heading-shape guards and clean title-vs-body ambiguity |

## Runtime Label Decision

- Keep `heading`, `paragraph`, `caption`, `table_like`, `list_item`, `footer_header_noise`, and `keep_as_text` as candidate hints only behind precision gates.
- Keep `page_number_noise` and `uncertain` out of direct runtime action until dedicated evidence exists.
- Keep `form_row`, `link_text`, `code_like`, `separator`, and `footnote_like` report-only.
