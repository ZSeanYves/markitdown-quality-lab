# PDF Model Training

This directory contains training/eval-only assets for the PDF layout classifier:

* `manifest.tsv` plus manual labels
* `scripts/` for export/train/eval helpers
* `datasets/` for tracked metadata or tiny subsets
* `models/` for tracked model JSON snapshots
* `reports/` and `evaluation/` for training/eval outputs and notes
* `archive/` for migration notes and legacy references

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
* the external quality corpus payloads live in `../external_quality`
* the main repository still provides the native MoonBit export/infer tool

Typical smoke:

```bash
python3 markitdown-quality-lab/pdf_model_training/scripts/export_manifest_features.py \
  --manifest markitdown-quality-lab/pdf_model_training/manifest.tsv \
  --corpus-root markitdown-quality-lab/external_quality \
  --sample-id heading_basic \
  --output-dir .tmp/pdf_model_training/post_migration_smoke
```

This directory is for model-training research only. It is not a runtime
dependency of the main repository, and this migration does not imply active
runtime integration.
