# DocLayNet Local Acquisition Plan

## Purpose

This plan defines how to acquire and use a larger local-only `DocLayNet`
working set for Task A teacher training without committing raw dataset bytes.

`DocLayNet` remains the primary gold source for:

- `Task A: convert_block_classification`
- layer: `convert/pdf`

## Recommended Local Path

Store local payloads under:

```text
pdf_model_training/local_only/datasets/doclaynet/
```

Suggested local layout:

```text
pdf_model_training/local_only/datasets/doclaynet/
  core/
    COCO/
    PNG/
  extra/
    PDF/
    JSON/
  manifests/
    source_manifest.local.tsv
    subset_manifest.local.tsv
```

Nothing under this tree should be committed except the tracked top-level
`local_only/README.md`.

## Scale Tiers

### Smoke

- size: `10-50` pages
- purpose: adapter and schema sanity
- expected use: verify mapping, bbox parsing, text-cell lookup, output shape

### Pilot

- size: `500-1000` pages
- purpose: first useful local-only Task A teacher experiments
- expected use: heading/paragraph/list/table/caption/noise coverage sanity

### Stronger Teacher

- size: `3000-5000` pages
- purpose: stronger offline teacher rounds and more stable error analysis
- expected use: heavier teacher training, ablations, and distillation prep

## Split Recommendation

Keep `DocLayNet` gold splits separate and explicit.

Recommended local teacher split framing:

- `train`
- `dev`
- `heldout`

Possible mapping from original dataset:

- original `train` -> local `train`
- original `val` -> local `dev`
- original `test` -> local `heldout` or reserve-only

Do not blend `DocLayNet` gold rows with `PubLayNet` weak rows into a single
"gold" eval split.

## Source And Version Recording

For each local acquisition round, record:

- source URL;
- dataset version or release identifier;
- license reference;
- acquisition date;
- local file hashes for the subset manifests;
- sampling notes.

Suggested local-only manifest fields:

- `dataset`
- `source_url`
- `license`
- `local_relpath`
- `sha256`
- `bytes`
- `split`
- `notes`

This manifest is local-only and should not be committed.

## Sampling Guidance

The subset should preserve useful coverage of high-value Task A labels:

- `Text`
- `Title`
- `Section-header`
- `List-item`
- `Caption`
- `Table`
- `Page-header`
- `Page-footer`

For stronger rounds, monitor that the selected pages are not dominated by only
one document category such as scientific articles or manuals.

## Rare Label Handling

The following labels should not dominate sampling, but should be explicitly
tracked when present:

- `Formula`
- `Picture`
- `Footnote`

Recommended handling:

- keep them in the local acquisition manifests;
- review them separately during adapter export;
- do not let them silently collapse into `paragraph`.

## Text Cells

Preferred training-time path:

- use `extra/JSON` text cells when available;
- keep empty text rows explicit when text-cell JSON is missing;
- record `missing_text_cells` or overlap failures in adapter notes.

Text-cell absence should not cause silent row loss during the raw adapter stage.

## Adapter Command

Recommended local-only adapter path:

```bash
python3 markitdown-quality-lab/pdf_model_training/text_block_classifier/adapters/doclaynet_adapter.py \
  --annotations pdf_model_training/local_only/datasets/doclaynet/core/COCO/train.json \
  --text-cells-root pdf_model_training/local_only/datasets/doclaynet/extra/JSON \
  --mapping markitdown-quality-lab/pdf_model_training/text_block_classifier/adapters/doclaynet_mapping.tsv \
  --output .tmp/doclaynet_task_a_train.tsv \
  --split train
```

The adapter output should remain local-only until it has been reviewed and a
future manifest draft is defined.

## Weak-Label Boundary

`DocLayNet` gold rows should remain distinct from:

- `PubLayNet` weak layout labels;
- `PubTables-1M` table specialists;
- historical small manual labels.

Teacher training may combine them later under controlled weighting, but gold
evaluation must stay clearly separated.
