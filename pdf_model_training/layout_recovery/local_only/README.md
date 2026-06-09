# Local-Only Training Data

This directory is reserved for local-only PDF model research payloads.

Examples:

- local public-dataset subsets;
- local adapter exports;
- local teacher-training feature dumps;
- local teacher checkpoints;
- local-only evaluation artifacts.

Recommended structure:

```text
local_only/
  datasets/
  artifacts/
  manifests/
```

Do not commit raw dataset bytes, local manifests, feature dumps, checkpoints,
or local eval outputs from this directory.

Only this `README.md` is intended to stay tracked in git.

Canonical path:

```text
pdf_model_training/layout_recovery/local_only/
```

Historical path name:

```text
pdf_model_training/layout_recovery_model/local_only/
```
