# PubTables Specialist Audit

This note scopes `PubTables-1M` as a local-only specialist source for
`text_block_classifier`. It is intentionally separate from the main
`DocLayNet` gold route.

## Source Summary

* `source_id`: `pubtables_1m`
* official code/source page:
  * `https://github.com/microsoft/table-transformer`
  * `https://msropendata.com/datasets/505fcbe3-1383-42b1-913a-f651b8b712d3`
* alternate mirror mentioned by the official repo:
  * `https://huggingface.co/datasets/bsmock/pubtables-1m`

## License and Redistribution

* The GitHub repository itself is under the MIT license.
* The dataset bytes are hosted through Microsoft Research Open Data and are not
  yet cleared here as tracked bytes.
* Repo policy for this project remains:
  * keep only metadata in git
  * keep any real dataset bytes under `local_only`
  * do not claim the dataset is cleared for tracked redistribution until the
    dataset-side usage terms are manually rechecked from the official data page

## What the Source Provides

The official `Table Transformer` README describes `PubTables-1M` as a table
dataset for table detection, table structure recognition, and functional
analysis. The published artifacts include:

* page-level table detection annotations
* page-word JSON with bounding boxes and text
* cropped-table structure annotations
* cropped-table word JSON
* PDF-coordinate table annotations
* row / column / cell / header structure inside tables

This is strong supervision for table regions and table internals, not a full
page-wide text-block label source.

## Task A Fit

Directly suitable:

* `table_like`

Potentially useful only as weak or derived signals:

* `caption`
* paragraph-like hard negatives near tables

Not a direct gold source for:

* `keep_as_text`
* `paragraph`
* `heading`
* `list_item`
* `footer_header_noise`

Reason: the source does not provide page-wide gold text-block labels aligned to
Task A. It gives strong table boxes, table words, and table structure, but not
reliable block labels for every non-table region on the page.

## Caption Caveat

`PubTables-1M` should not currently be treated as direct gold supervision for
`caption`.

What it can support:

* mining nearby short text as local-only weak caption candidates
* testing whether caption lexical cues plus table proximity improve teacher
  behavior

What it must not support:

* claiming `caption` gold labels equivalent to `DocLayNet`
* mixing derived caption candidates into `DocLayNet` heldout evaluation

## Leakage Guardrails

The following source-only fields may be used as supervision in a specialist
adapter, but must not become inference-time features for the final block model:

* source XML object labels such as `table`
* PDF/structure annotation object types
* cell/header functional labels
* any field that exists only because the page came from `PubTables-1M`
* any label-derived neighbor features from heldout rows

Allowed inference-time features remain the same family used by the current
DocLayNet baseline:

* text
* bbox geometry
* page position
* block ordering
* neighbor gaps and alignment derived only from observable layout

## Specialist Role

* `role`: `specialist`
* primary target labels: `table_like`
* optional weak probe: `caption`
* eval policy:
  * never mix into `DocLayNet` gold heldout
  * never present specialist-only results as Task A gold quality
  * keep source identity explicit in any mixed training experiment

## Local-Only Storage Plan

Dataset bytes:

```text
pdf_model_training/text_block_classifier/local_only/datasets/pubtables_1m/
```

Adapter outputs:

```text
pdf_model_training/text_block_classifier/local_only/adapter_outputs/pubtables_1m/<subset_id>/task_a_rows.tsv
```

Specialist features / artifacts:

```text
pdf_model_training/text_block_classifier/local_only/features/pubtables_1m/
pdf_model_training/text_block_classifier/local_only/artifacts/pubtables_1m/
pdf_model_training/text_block_classifier/local_only/reports/pubtables_1m/
```

## Adapter Output Schema

Keep the same 13-column adapter schema used by the current Task A pipeline:

* `sample_id`
* `source_dataset`
* `source_page_id`
* `source_region_id`
* `page_no`
* `bbox`
* `source_label`
* `target_label`
* `target_task`
* `text`
* `confidence`
* `split`
* `notes`

For a first `PubTables` specialist pass:

* positive rows: table regions mapped to `table_like`
* optional weak rows: nearby short text blocks marked clearly as weak
* no claim that non-table page regions are exhaustively labeled

## Download Strategy

This round does not require a full download.

Recommended next step:

1. keep the current tracked metadata and tiny first-row previews
2. if needed, download only a tiny local-only smoke subset first
3. after schema sanity, stage a larger local-only table subset
4. keep all bytes and derived outputs under `local_only`

## Recommendation

Use `PubTables-1M` as a `table_like` specialist and a possible weak caption
probe. Do not treat it as a replacement for `DocLayNet` gold evaluation, and do
not mix it into heldout metrics.
