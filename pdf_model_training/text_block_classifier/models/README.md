# Legacy Model Metadata

This directory keeps historical tracked JSON metadata from the earlier
`pdf_layout_classifier` training spike.

Important interpretation:

* names such as `pdf_layout_linear_*` and `round*.json` are legacy names
* despite the `layout` name, these files are closer to early text block
  classification experiments than to the current parser/layout recovery route
* some of these historical models were trained from mixed manifests that
  contained both block and boundary records
* these files are reference metadata only

Do not treat these files as:

* the current recommended training route
* the current `HGB` teacher line
* distillation v0 or v1 artifacts
* runtime candidates

Current recommended line:

* `DocLayNet` adapters and pilot subsets under `local_only/`
* `scripts/build_doclaynet_baseline_features.py`
* `scripts/train_doclaynet_baseline.py`
* `scripts/export_hgb_distilled_hints.py`
* `training/distillation_policy.md`
* `training/roadmap.md`
