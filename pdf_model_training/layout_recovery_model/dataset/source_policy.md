# Layout Recovery Model Source Policy

Tracked content may include:

* dataset registry and source metadata
* adapter specifications
* label mappings
* active manifest headers

Local-only content should include:

* larger adapted public-dataset subsets
* teacher features, checkpoints, prediction dumps, and eval artifacts

Recommended local-only root:

```text
pdf_model_training/layout_recovery_model/local_only/
```

Use mature public annotated layout datasets first:

* `DocLayNet` as the preferred gold region source
* `PubLayNet` as a weak layout supplement
* `PubTables-1M` as a table-region specialist

Hard boundaries:

* do not promote repo-manual boundary rows as the active manifest
* do not flatten layout recovery into text block semantics
* do not commit local-only dataset bytes or teacher artifacts
