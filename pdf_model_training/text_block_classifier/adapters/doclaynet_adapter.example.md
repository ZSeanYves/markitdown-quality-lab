# DocLayNet Adapter Usage

This is a local-only usage note for `text_block_classifier/adapters/`.

Do not commit:

* raw DocLayNet COCO files
* raw DocLayNet PNG / PDF / JSON payloads
* adapter outputs generated from real DocLayNet data

## Example Command

```bash
python3 markitdown-quality-lab/pdf_model_training/text_block_classifier/adapters/doclaynet_adapter.py \
  --annotations /path/to/DocLayNet_core/COCO/train.json \
  --text-cells-root /path/to/DocLayNet_extra/JSON \
  --mapping markitdown-quality-lab/pdf_model_training/text_block_classifier/adapters/doclaynet_mapping.tsv \
  --output .tmp/doclaynet_task_a_preview.tsv \
  --split train \
  --max-rows 100
```

## Smoke Without Text Cells

```bash
python3 markitdown-quality-lab/pdf_model_training/text_block_classifier/adapters/doclaynet_adapter.py \
  --annotations /path/to/DocLayNet_core/COCO/train.json \
  --mapping markitdown-quality-lab/pdf_model_training/text_block_classifier/adapters/doclaynet_mapping.tsv \
  --output .tmp/doclaynet_task_a_preview.tsv \
  --split train \
  --max-rows 20
```

If you omit text cells:

* `text` will be empty
* `notes` will include `missing_text_cells`

## Synthetic Fixture Smoke

```bash
python3 markitdown-quality-lab/pdf_model_training/text_block_classifier/adapters/doclaynet_adapter.py \
  --annotations markitdown-quality-lab/pdf_model_training/text_block_classifier/adapters/testdata/doclaynet_adapter_minicoco.json \
  --text-cells-root markitdown-quality-lab/pdf_model_training/text_block_classifier/adapters/testdata/doclaynet_adapter_minicells \
  --mapping markitdown-quality-lab/pdf_model_training/text_block_classifier/adapters/doclaynet_mapping.tsv \
  --output .tmp/doclaynet_adapter_test.tsv \
  --split train \
  --max-rows 10
```
