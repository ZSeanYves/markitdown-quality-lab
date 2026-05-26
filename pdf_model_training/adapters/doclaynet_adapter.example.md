# DocLayNet Adapter Usage

## Purpose

This file shows how to run the local-only DocLayNet Task A adapter once you
already have DocLayNet bytes on your own machine.

Do not commit:

- raw DocLayNet `COCO/*.json`;
- raw DocLayNet `PNG/`, `PDF/`, or `JSON/` assets;
- adapter outputs generated from real DocLayNet data.

## Example Local Paths

Example local layout:

```text
/path/to/DocLayNet_core/COCO/train.json
/path/to/DocLayNet_core/COCO/val.json
/path/to/DocLayNet_extra/JSON/<page-stem>.json
```

## Example Command

```bash
python3 markitdown-quality-lab/pdf_model_training/adapters/doclaynet_adapter.py \
  --annotations /path/to/DocLayNet_core/COCO/train.json \
  --text-cells-root /path/to/DocLayNet_extra/JSON \
  --mapping markitdown-quality-lab/pdf_model_training/adapters/doclaynet_mapping.tsv \
  --output .tmp/doclaynet_task_a_preview.tsv \
  --split train \
  --max-rows 100
```

## Smoke Without Text Cells

If you do not have the extra JSON text cells yet:

```bash
python3 markitdown-quality-lab/pdf_model_training/adapters/doclaynet_adapter.py \
  --annotations /path/to/DocLayNet_core/COCO/train.json \
  --mapping markitdown-quality-lab/pdf_model_training/adapters/doclaynet_mapping.tsv \
  --output .tmp/doclaynet_task_a_preview.tsv \
  --split train \
  --max-rows 20
```

In that case:

- `text` will be empty;
- `notes` will include `missing_text_cells`.

## Expected Output Fields

The adapter writes TSV with these fields:

```text
sample_id
source_dataset
source_page_id
source_region_id
page_no
bbox
source_label
target_label
target_task
text
confidence
split
notes
```

## Ignore / Uncertain Policy

Default behavior:

- `Formula` and `Picture` rows are skipped because the current mapping marks
  them as non-training `uncertain`.
- `Footnote` is still emitted, but `notes` marks it as `use_for_training=review`.

To include skipped rows for audit:

```bash
python3 markitdown-quality-lab/pdf_model_training/adapters/doclaynet_adapter.py \
  --annotations /path/to/DocLayNet_core/COCO/train.json \
  --mapping markitdown-quality-lab/pdf_model_training/adapters/doclaynet_mapping.tsv \
  --output .tmp/doclaynet_task_a_with_ignored.tsv \
  --split train \
  --include-ignored
```

## Synthetic Fixture Smoke

This repo includes a tiny synthetic fixture for parser testing only:

```bash
python3 markitdown-quality-lab/pdf_model_training/adapters/doclaynet_adapter.py \
  --annotations markitdown-quality-lab/pdf_model_training/adapters/testdata/doclaynet_adapter_minicoco.json \
  --text-cells-root markitdown-quality-lab/pdf_model_training/adapters/testdata/doclaynet_adapter_minicells \
  --mapping markitdown-quality-lab/pdf_model_training/adapters/doclaynet_mapping.tsv \
  --output .tmp/doclaynet_adapter_test.tsv \
  --split train \
  --max-rows 10
```

The synthetic fixture is project-owned fake data and does not contain any real
DocLayNet bytes.
