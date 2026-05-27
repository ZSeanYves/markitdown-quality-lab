# Shared Script Notes

This directory should only contain scripts that are still genuinely shared
across PDF model-training targets.

Current shared scripts:

* `path_roots.py`
* `fetch_tiny_subsets.py`

## Boundary

`fetch_tiny_subsets.py` is still only a tiny-metadata helper. It is not:

* a full dataset downloader
* a larger local-only acquisition tool
* a teacher-training downloader
* a license validator

Block-only train/eval/export scripts now live under:

* `text_block_classifier/scripts/`

If a future layout-recovery-specific script appears, it should live under:

* `layout_recovery_model/scripts/`
