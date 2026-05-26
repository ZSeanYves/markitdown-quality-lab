# DocLayNet Task A Adapter Design

## Purpose

This adapter design defines how `DocLayNet` can feed
`PDF text-flow assist model` Task A:

- task: `convert_block_classification`
- layer: `convert/pdf`

The adapter is a data-preparation bridge only. It is not a training entrypoint,
and it does not modify the active manifest.

## Why DocLayNet

`DocLayNet` is currently the strongest public gold-layout source for Task A
because it is:

- human-annotated;
- layout-diverse across manuals, scientific articles, finance, patents, laws,
  and tenders;
- distributed with COCO layout annotations;
- paired, in the full dataset, with single-page PDFs and JSON text cells.

## Inputs

The full dataset provides four relevant asset types:

1. page PNG images;
2. COCO layout annotations;
3. extra single-page PDF files;
4. extra JSON files with digital text cells and coordinates.

For adapter work, the preferred input priority is:

1. COCO annotations for source labels and bboxes;
2. JSON text cells for text recovery;
3. PDF page metadata for provenance and page indexing;
4. PNG only as a fallback for visualization or audit, not as a text source.

## Recommended Output

The recommended normalized output is TSV or JSONL with one adapted region per row.

Recommended fields:

- `sample_id`
- `source_dataset`
- `source_page_id`
- `source_region_id`
- `page_no`
- `bbox`
- `source_label`
- `target_label`
- `target_task`
- `text`
- `confidence`
- `split`
- `notes`

TSV is preferred for lightweight audit and manifest-adjacent review.
JSONL is acceptable for richer intermediate adapter output.

## Field Semantics

- `sample_id`: stable adapter row id, for example
  `doclaynet_<split>_<image_id>_<annotation_id>`.
- `source_dataset`: always `doclaynet`.
- `source_page_id`: original DocLayNet image/page id.
- `source_region_id`: original COCO annotation id.
- `page_no`: original page number from the image metadata.
- `bbox`: normalized or original bbox serialized as `x,y,w,h`.
- `source_label`: original DocLayNet class name.
- `target_label`: mapped Task A label or `uncertain`.
- `target_task`: always `convert_block_classification`.
- `text`: recovered text from page JSON cells when available.
- `confidence`: mapping confidence, not model confidence.
- `split`: `train`, `val`, or `test` from DocLayNet.
- `notes`: adapter caveats such as missing text, partial overlap, or review flags.

## Mapping Rules

### Positive Task A Training Labels

Use these source labels directly for Task A training:

- `Title` -> `heading`
- `Section-header` -> `heading`
- `Text` -> `paragraph`
- `List-item` -> `list_item`
- `Caption` -> `caption`
- `Page-header` -> `footer_header_noise`
- `Page-footer` -> `footer_header_noise`
- `Table` -> `table_like`

### Review or Restricted Labels

- `Footnote` -> `keep_as_text`
  This is useful text, but should stay review-gated at first because some
  footnotes may be citation noise or layout-specific marginal text.

- `Formula` -> `uncertain`
  Do not coerce formulas into `paragraph`. If we later want formula-aware
  handling, it should be a deliberate schema extension or explicit ignore path.

- `Picture` -> `uncertain`
  Picture regions are non-text layout context. They can help negative sampling
  or exclusion logic, but they are not direct Task A text-flow labels.

## Text Recovery Strategy

Preferred strategy:

1. load page JSON text cells;
2. match text cells to COCO regions by bbox overlap;
3. concatenate matched cells in reading order;
4. store recovered text in `text`.

If page JSON is missing:

- keep the row, but set `text` empty;
- add a `notes` marker such as `missing_text_cells`;
- do not drop the row automatically unless the downstream training path requires
  text-bearing rows only.

## Handling Specific Label Types

### Missing Text

- empty `text` is allowed in adapter output;
- rows with empty `text` should be filtered later by a task-specific export
  policy, not silently lost in the raw adapter stage.

### Figure / Picture Labels

- keep `Picture` rows available in raw adapter output if useful for auditing;
- do not treat them as positive Task A training rows by default.

### Formula Labels

- keep as `uncertain` or route to ignore during training export;
- never flatten into `paragraph`.

### Page Headers / Footers

- map both to `footer_header_noise`;
- retain `page_no` and source bbox to help later repeated-region heuristics.

### List / Table / Caption

- these are high-value labels and should remain explicit;
- do not collapse `List-item` into `paragraph`;
- do not collapse `Caption` into `paragraph`;
- keep `Table` separate as `table_like`.

### Uncertain Mapping

Use `target_label=uncertain` when:

- the source label is non-text or outside current Task A label space;
- text recovery is missing and the semantic label cannot be safely reused;
- a future schema split is likely.

## Split Handling

Use DocLayNet's original splits first:

- `train`
- `val`
- `test`

For local Task A work:

- `train` can remain `train`;
- `val` can become `heldout` or stay `val` in an adapter-intermediate file;
- `test` should stay out of ad-hoc local tuning unless we define a clean policy.

Do not merge DocLayNet gold rows with weak-label sources in one flat export
without preserving the source dataset and confidence fields.

## Why This Does Not Enter Active Manifest Yet

Do not add DocLayNet rows directly to active `manifest.tsv` / `manifest.v2.tsv`
yet because:

- the repo currently only tracks metadata, not local DocLayNet annotations;
- we still need a concrete adapter implementation for text-cell alignment;
- split policy between gold and weak sources is not finalized;
- `Footnote`, `Formula`, and `Picture` still need explicit export behavior.

## Tiny Subset Policy Interaction

This adapter is compatible with the current tiny subset policy:

- metadata and loader files may be tracked;
- tiny annotation previews are only acceptable if they are small, rights-clean,
  and provenance-recorded;
- full dataset bytes must remain out of the repo.

## Path Into Future Manifest Intake

The expected path is:

1. keep `DocLayNet` in `dataset_audit.tsv` as primary Task A source;
2. finalize mapping in `doclaynet_mapping.tsv`;
3. implement a local-only adapter script against downloaded local dataset bytes;
4. export adapter rows into a reviewed intermediate TSV/JSONL;
5. define a gold-only Task A manifest draft;
6. only then consider adding reviewed rows into a future manifest draft.
