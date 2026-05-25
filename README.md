# markitdown-quality-lab

External quality corpus payloads and PDF model-training assets for
`markitdown`.

This sibling working tree is not a release artifact of the main repository.
The main repo reads it through:

* `MARKITDOWN_QUALITY_LAB`
* `MARKITDOWN_QUALITY_CORPUS`
* `MARKITDOWN_LAYOUT_LAB`
* `MARKITDOWN_LAYOUT_MODEL`

Normal conversion runtime does not depend on this tree.

Preferred local deployment is repo-local:

```bash
cd /path/to/markitdown
git clone git@github.com:ZSeanYves/markitdown-quality-lab.git markitdown-quality-lab
```

Top-level layout:

* `external_quality/`: format-first real-world quality corpus and migration staging
* `pdf_model_training/`: PDF layout-model training/eval assets only

Recommended entrypoints:

* `external_quality/_quality_rows_staging/manifest.tsv`
* `external_quality/ocr/_legacy_samples/`
* `external_quality/ocr/_audit/`
* `external_quality/pdf/_audit/`
* `pdf_model_training/manifest.tsv`
* `pdf_model_training/scripts/`

This repo is currently in a structure-cleanup phase. The recommended paths are
the new `external_quality/` and `pdf_model_training/` roots; archive or
staging trees may still mention legacy paths for migration context.
