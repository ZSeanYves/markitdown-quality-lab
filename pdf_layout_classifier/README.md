# PDF Layout Classifier Lab

This directory contains training/eval-only assets for the PDF layout classifier:

* manifest + labels
* scripts
* local feature/eval outputs
* model artifacts
* optional datasets

Normal PDF conversion in the main repository does not depend on these assets.
The runtime gate remains distilled MoonBit logic in `convert/pdf`.

## Script entrypoints

Preferred training/eval entrypoints now live here:

* `scripts/export_manifest_features.py`
* `scripts/local_eval.py`
* `scripts/train.py`
* `scripts/fetch_tiny_subsets.py`
* `scripts/export_features.sh`
* `scripts/evaluate.sh`

These scripts assume:

* the main repository lives one directory above this lab
* the quality corpus payloads live in `../corpus`
* the main repository still provides the native MoonBit export/infer tool

Typical smoke:

```bash
python3 markitdown-quality-lab/pdf_layout_classifier/scripts/export_manifest_features.py \
  --manifest markitdown-quality-lab/pdf_layout_classifier/manifest.tsv \
  --corpus-root markitdown-quality-lab/corpus \
  --sample-id heading_basic \
  --output-dir .tmp/pdf_layout_classifier/post_migration_smoke
```
